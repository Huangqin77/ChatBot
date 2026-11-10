from sqlalchemy import event, inspect
from sqlmodel import SQLModel, Session, create_engine, select

from .models import Bot, Room, RoomBot, Message, Task, ToolCall, now


def make_engine(url: str):
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 15})

    @event.listens_for(engine, 'connect')
    def configure(dbapi_connection, _):
        dbapi_connection.execute('PRAGMA foreign_keys=ON')
        dbapi_connection.execute('PRAGMA journal_mode=WAL')
    return engine


def initialize(engine):
    SQLModel.metadata.create_all(engine)
    with engine.begin() as connection:
        # Additive migration for databases created before native call IDs were recorded.
        if 'provider_call_id' not in {c['name'] for c in inspect(connection).get_columns('tool_calls')}:
            connection.exec_driver_sql('ALTER TABLE tool_calls ADD COLUMN provider_call_id VARCHAR')
    with Session(engine) as session:
        # A process restart must not leave interrupted runs looking active forever.
        for row in session.exec(select(Task).where(Task.status == 'running')).all():
            row.status, row.error, row.completed_at = 'failed', '服务重启，任务已中断，请重新发送。', now()
            session.add(row)
        for row in session.exec(select(ToolCall).where(ToolCall.status == 'running')).all():
            row.status, row.output, row.completed_at = 'failed', '服务重启，工具执行中断。', now()
            session.add(row)
        if not session.exec(select(Room)).first():
            room = Room(name='协作实验室', description='与 AI 队友一起，把想法变成结果。')
            planner = Bot(name='策划官', role='任务拆解与协作统筹',
                          system_prompt='你是策划官，擅长拆解任务、委派给同事，并基于真实工具结果总结。涉及计算时可以委派给计算员。请使用中文。',
                          tools=['calculator', 'get_current_time', 'delegate_to_bot'])
            analyst = Bot(name='计算员', role='计算、核验与数据分析',
                          system_prompt='你是计算员，数学计算必须使用 calculator 工具，时间必须使用 get_current_time。请准确、简洁地回答。',
                          tools=['calculator', 'get_current_time'])
            session.add_all([room, planner, analyst])
            session.flush()
            session.add_all([RoomBot(room_id=room.id, bot_id=x.id) for x in [planner, analyst]])
            session.add(Message(room_id=room.id, kind='system', sender_name='系统',
                                content='欢迎来到协作实验室。邀请队友加入，或 @Bot 开始一个任务。Demo 模式使用规则演示，工具由服务端真实执行。'))
        session.commit()
