import Header from './components/Header'
import Hero from './components/Hero'
import Features from './components/Features'
import Workflow from './components/Workflow'
import UseCases from './components/UseCases'
import FAQ from './components/FAQ'
import Footer from './components/Footer'

export default function App() {
  return <div id="home" className="min-h-screen bg-white"><a className="skip-link" href="#main">跳到主要内容</a><Header /><main id="main"><Hero /><Features /><Workflow /><UseCases /><FAQ /></main><Footer /></div>
}
