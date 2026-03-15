'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Zap, Brain, Home, Terminal, Database, Shield, Sparkles, 
  Send, Bot, User, Cpu, Network, MessageSquare, 
  ChevronRight, Github, ExternalLink,
  Activity, Server
} from 'lucide-react'

const llmProviders = [
  { name: 'GLM-4.5-air', icon: '⚡', cost: '$0.00/1M', type: 'fast', color: 'bg-emerald-500' },
  { name: 'GLM-4.7-Flash', icon: '🚀', cost: '$0.05/1M', type: 'balanced', color: 'bg-sky-500' },
  { name: 'Gemini-2.5-flash', icon: '🧠', cost: '$0.15/1M', type: 'smart', color: 'bg-violet-500' },
  { name: 'Groq Llama-3.3', icon: '🔥', cost: '$0.10/1M', type: 'fast', color: 'bg-orange-500' },
  { name: 'GLM-4.7', icon: '💎', cost: '$0.20/1M', type: 'smart', color: 'bg-blue-500' },
  { name: 'Ollama-local', icon: '🏠', cost: '$0.00', type: 'offline', color: 'bg-slate-500' },
]

const features = [
  { icon: Network, title: 'Smart LLM Routing', description: 'Автоматический выбор модели по сложности запроса — от быстрого GLM до мощного Gemini', color: 'text-emerald-500' },
  { icon: Database, title: 'RAG Память', description: 'Векторная память на Qdrant с sentence-transformers для контекстных диалогов', color: 'text-violet-500' },
  { icon: Sparkles, title: 'Самообучение', description: 'Изучай новые темы командой learn: тема — знания сохраняются в векторную БД', color: 'text-amber-500' },
  { icon: Terminal, title: 'Shell Команды', description: 'Прямое выполнение системных команд через exec с подтверждением безопасности', color: 'text-sky-500' },
  { icon: Shield, title: 'YOLO Режим', description: 'Автовыполнение команд без подтверждений для опытных пользователей', color: 'text-rose-500' },
  { icon: Home, title: 'Offline Fallback', description: 'Работает без интернета через Ollama — полная независимость от облака', color: 'text-slate-500' }
]

const commands = [
  { cmd: 'exec <команда>', desc: 'Выполнить shell команду', example: 'exec ls -la' },
  { cmd: 'learn: <тема>', desc: 'Изучить и записать в память', example: 'learn: квантовые вычисления' },
  { cmd: 'yolo', desc: 'Вкл/выкл автовыполнение', example: 'yolo' },
  { cmd: 'статус', desc: 'Диагностика системы', example: 'статус' },
  { cmd: 'нет / отмена', desc: 'Отменить команду', example: 'нет' },
  { cmd: 'выход', desc: 'Выход из агента', example: 'выход' },
]

const demoChatMessages = [
  { role: 'assistant', content: 'Привет! Я Vika_Ok — твой персональный AI-агент. Могу помочь с задачами, выполнить команды или изучить новую тему. Что хочешь сделать?', model: 'GLM-4.5-air' },
  { role: 'user', content: 'Расскажи о своих возможностях' },
  { role: 'assistant', content: 'У меня 6 ключевых возможностей:\n\n⚡ **Smart Routing** — выбираю оптимальную модель по сложности\n🧠 **RAG память** — помню контекст наших разговоров\n✨ **Самообучение** — могу изучить любую тему\n💻 **Shell** — выполняю системные команды\n🛡️ **YOLO режим** — автовыполнение без подтверждений\n🏠 **Offline** — работаю через Ollama без интернета', model: 'Gemini-2.5-flash' },
  { role: 'user', content: 'learn: Rust programming' },
  { role: 'assistant', content: '🔍 Изучаю тему "Rust programming"...\n\n📚 Источники обработаны: 15 статей, 3 документации\n💾 Сохранено в векторную память: 127 чанков\n✅ Готово! Теперь могу отвечать на вопросы по Rust с использованием изученного материала.', model: 'Gemini-2.5-flash' },
]

interface Message {
  role: 'user' | 'assistant'
  content: string
  model?: string
  timestamp: Date
}

export default function VikaOkDemo() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [currentModel, setCurrentModel] = useState('GLM-4.5-air')
  const [activeTab, setActiveTab] = useState('demo')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return
    const userMessage: Message = { role: 'user', content: input, timestamp: new Date() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)
    setTimeout(() => {
      let model = 'GLM-4.5-air'
      const complexIndicators = ['объясни', 'разбер', 'анализ', 'сравн', 'как работает', 'почему', 'learn:']
      const isComplex = complexIndicators.some(ind => input.toLowerCase().includes(ind))
      if (isComplex) model = 'Gemini-2.5-flash'
      setCurrentModel(model)
      const responses: { [key: string]: string } = {
        'привет': 'Привет! Я Vika_Ok — твой AI-агент. Чем могу помочь?',
        'статус': '📊 **Статус системы:**\n\n✅ GLM-4.5-air — онлайн\n✅ Gemini-2.5-flash — онлайн\n✅ Qdrant — подключен\n✅ Ollama — готов (fallback)',
        'yolo': '🔥 **YOLO режим активирован!**\n\nТеперь команды выполняются автоматически.',
        'help': '📖 **Доступные команды:**\n\n• exec <команда> — выполнить shell\n• learn: <тема> — изучить тему\n• yolo — автовыполнение\n• статус — диагностика',
      }
      let response = responses[input.toLowerCase()]
      if (!response) {
        if (input.toLowerCase().startsWith('learn:')) {
          const topic = input.replace(/learn:\s*/i, '')
          response = `🔍 Изучаю тему "${topic}"...\n\n✅ Тема изучена и добавлена в базу знаний!`
        } else if (input.toLowerCase().startsWith('exec ')) {
          const cmd = input.replace('exec ', '')
          response = `💻 Выполняю: \`${cmd}\`\n\n⚠️ В демо-режиме команды не выполняются.`
        } else {
          response = `Понял! В демо-режиме показываю возможности Vika_Ok.\n\nДля полного функционала запусти agent.py локально.`
        }
      }
      setMessages(prev => [...prev, { role: 'assistant', content: response, model, timestamp: new Date() }])
      setIsTyping(false)
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <header className="sticky top-0 z-50 border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-xl font-bold">V</div>
            <div>
              <h1 className="font-bold text-lg">Vika_Ok <span className="text-violet-400">v8.3</span></h1>
              <p className="text-xs text-slate-400">Боевой AI-агент</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20"><Activity className="w-3 h-3 mr-1" />Online</Badge>
            <a href="https://github.com/Redrock453/vika_ok" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition-colors"><Github className="w-5 h-5" /></a>
          </div>
        </div>
      </header>

      <section className="container mx-auto px-4 py-16">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <Badge className="mb-4 bg-violet-500/10 text-violet-400 border-violet-500/20"><Sparkles className="w-3 h-3 mr-1" />Персональный AI-агент</Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white via-violet-200 to-fuchsia-200 bg-clip-text text-transparent">Умный роутинг LLM с RAG-памятью</h2>
          <p className="text-lg text-slate-400 mb-8">6 провайдеров, автовыбор по сложности, векторная память и самообучение.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Button size="lg" className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500" onClick={() => setActiveTab('interactive')}><Terminal className="w-4 h-4 mr-2" />Попробовать демо</Button>
            <a href="https://github.com/Redrock453/vika_ok" target="_blank" rel="noopener noreferrer"><Button size="lg" variant="outline" className="border-slate-700"><Github className="w-4 h-4 mr-2" />GitHub<ExternalLink className="w-3 h-3 ml-2" /></Button></a>
          </div>
        </div>

        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur mb-12">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Network className="w-5 h-5 text-violet-400" />Smart LLM Routing</CardTitle>
            <CardDescription>Автоматический выбор модели в зависимости от сложности запроса</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <div className="flex items-center gap-2 mb-2"><Zap className="w-5 h-5 text-emerald-400" /><span className="font-semibold text-emerald-400">Простой запрос</span></div>
                <p className="text-sm text-slate-400 mb-2">Привет, как дела?</p>
                <div className="flex items-center gap-2 text-sm"><span className="text-2xl">⚡</span><span className="font-medium">GLM-4.5-air</span><Badge variant="outline" className="ml-auto border-emerald-500/20 text-emerald-400">$0.00/1M</Badge></div>
              </div>
              <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                <div className="flex items-center gap-2 mb-2"><Brain className="w-5 h-5 text-violet-400" /><span className="font-semibold text-violet-400">Сложный запрос</span></div>
                <p className="text-sm text-slate-400 mb-2">Объясни квантовые вычисления</p>
                <div className="flex items-center gap-2 text-sm"><span className="text-2xl">🧠</span><span className="font-medium">Gemini-2.5-flash</span><Badge variant="outline" className="ml-auto border-violet-500/20 text-violet-400">$0.15/1M</Badge></div>
              </div>
              <div className="p-4 rounded-xl bg-slate-500/10 border border-slate-500/20">
                <div className="flex items-center gap-2 mb-2"><Home className="w-5 h-5 text-slate-400" /><span className="font-semibold text-slate-400">Нет интернета</span></div>
                <p className="text-sm text-slate-400 mb-2">Офлайн режим</p>
                <div className="flex items-center gap-2 text-sm"><span className="text-2xl">🏠</span><span className="font-medium">Ollama-local</span><Badge variant="outline" className="ml-auto border-slate-500/20 text-slate-400">$0.00</Badge></div>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-slate-800">
              <p className="text-sm text-slate-500 mb-3">Полная цепочка fallback:</p>
              <div className="flex flex-wrap items-center gap-2">
                {['GLM-4.5-air', 'GLM-4.7-Flash', 'Gemini', 'Groq', 'GLM-4.7', 'Ollama'].map((model, i) => (
                  <div key={model} className="flex items-center gap-2">
                    <Badge variant="outline" className="border-slate-700 text-slate-300">{model}</Badge>
                    {i < 5 && <ChevronRight className="w-4 h-4 text-slate-600" />}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="container mx-auto px-4 py-12">
        <h3 className="text-2xl font-bold text-center mb-8">Возможности</h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feature, i) => (
            <Card key={i} className="bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-colors group">
              <CardContent className="p-6">
                <feature.icon className={`w-8 h-8 ${feature.color} mb-3 group-hover:scale-110 transition-transform`} />
                <h4 className="font-semibold mb-2">{feature.title}</h4>
                <p className="text-sm text-slate-400">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="container mx-auto px-4 py-12">
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2"><MessageSquare className="w-5 h-5 text-violet-400" />Демо чат</CardTitle>
                <CardDescription>Интерактивная демонстрация возможностей Vika_Ok</CardDescription>
              </div>
              <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/20"><Cpu className="w-3 h-3 mr-1" />{currentModel}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                <TabsTrigger value="demo">Демо диалог</TabsTrigger>
                <TabsTrigger value="interactive">Интерактив</TabsTrigger>
                <TabsTrigger value="commands">Команды</TabsTrigger>
              </TabsList>
              <TabsContent value="demo">
                <div className="h-[400px] rounded-xl border border-slate-800 bg-slate-950/50 overflow-hidden">
                  <ScrollArea className="h-full p-4">
                    {demoChatMessages.map((msg, i) => (
                      <div key={i} className={`flex gap-3 mb-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-slate-700' : 'bg-gradient-to-br from-violet-500 to-fuchsia-500'}`}>
                          {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                          {msg.model && <Badge variant="outline" className="mb-1 text-xs border-slate-700 text-slate-500">{msg.model}</Badge>}
                          <div className={`p-3 rounded-xl text-sm whitespace-pre-wrap ${msg.role === 'user' ? 'bg-violet-600 text-white' : 'bg-slate-800 text-slate-200'}`}>
                            {msg.content.split('\n').map((line, j) => (<span key={j}>{line.split('**').map((part, k) => k % 2 === 1 ? <strong key={k}>{part}</strong> : part)}{j < msg.content.split('\n').length - 1 && <br />}</span>))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </ScrollArea>
                </div>
              </TabsContent>
              <TabsContent value="interactive">
                <div className="h-[400px] rounded-xl border border-slate-800 bg-slate-950/50 overflow-hidden flex flex-col">
                  <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                    {messages.length === 0 && (<div className="text-center text-slate-500 py-12"><Bot className="w-12 h-12 mx-auto mb-3 opacity-50" /><p>Начни диалог с Vika_Ok</p><p className="text-xs mt-2">Попробуй: &quot;привет&quot;, &quot;статус&quot;, &quot;help&quot;</p></div>)}
                    {messages.map((msg, i) => (
                      <div key={i} className={`flex gap-3 mb-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-slate-700' : 'bg-gradient-to-br from-violet-500 to-fuchsia-500'}`}>
                          {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                          {msg.model && <Badge variant="outline" className="mb-1 text-xs border-slate-700 text-slate-500">{msg.model}</Badge>}
                          <div className={`p-3 rounded-xl text-sm whitespace-pre-wrap ${msg.role === 'user' ? 'bg-violet-600 text-white' : 'bg-slate-800 text-slate-200'}`}>
                            {msg.content.split('\n').map((line, j) => (<span key={j}>{line.split('**').map((part, k) => k % 2 === 1 ? <strong key={k}>{part}</strong> : part)}{j < msg.content.split('\n').length - 1 && <br />}</span>))}
                          </div>
                        </div>
                      </div>
                    ))}
                    {isTyping && (<div className="flex gap-3 mb-4"><div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center"><Bot className="w-4 h-4" /></div><div className="p-3 rounded-xl bg-slate-800"><div className="flex gap-1"><span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0ms' }}></span><span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '150ms' }}></span><span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '300ms' }}></span></div></div></div>)}
                  </ScrollArea>
                  <div className="p-4 border-t border-slate-800">
                    <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2">
                      <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Введите сообщение..." className="bg-slate-800 border-slate-700 focus-visible:ring-violet-500" disabled={isTyping} />
                      <Button type="submit" disabled={isTyping || !input.trim()} className="bg-violet-600 hover:bg-violet-500"><Send className="w-4 h-4" /></Button>
                    </form>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="commands">
                <div className="rounded-xl border border-slate-800 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-800/50"><tr><th className="text-left p-3 font-medium text-slate-400">Команда</th><th className="text-left p-3 font-medium text-slate-400">Описание</th><th className="text-left p-3 font-medium text-slate-400 hidden md:table-cell">Пример</th></tr></thead>
                    <tbody className="divide-y divide-slate-800">
                      {commands.map((cmd, i) => (<tr key={i} className="hover:bg-slate-800/30"><td className="p-3"><code className="text-violet-400 bg-violet-500/10 px-2 py-1 rounded">{cmd.cmd}</code></td><td className="p-3 text-slate-400">{cmd.desc}</td><td className="p-3 text-slate-500 hidden md:table-cell"><code className="text-xs">{cmd.example}</code></td></tr>))}
                    </tbody>
                  </table>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </section>

      <section className="container mx-auto px-4 py-12">
        <h3 className="text-2xl font-bold text-center mb-8">Поддерживаемые LLM</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {llmProviders.map((provider, i) => (
            <Card key={i} className="bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-colors text-center">
              <CardContent className="p-4">
                <div className="text-3xl mb-2">{provider.icon}</div>
                <p className="font-medium text-sm mb-1">{provider.name}</p>
                <Badge variant="outline" className={`text-xs border-slate-700 ${provider.color.replace('bg-', 'text-')}`}>{provider.cost}</Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="container mx-auto px-4 py-12">
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader><CardTitle className="flex items-center gap-2"><Server className="w-5 h-5 text-emerald-400" />Быстрый старт</CardTitle></CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-xs">1</span>Установка</h4>
                <div className="bg-slate-950 rounded-lg p-4 font-mono text-sm">
                  <p className="text-emerald-400">git clone https://github.com/Redrock453/vika_ok.git</p>
                  <p className="text-emerald-400">cd vika_ok && pip install -r requirements.txt</p>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-xs">2</span>Конфигурация .env</h4>
                <div className="bg-slate-950 rounded-lg p-4 font-mono text-sm">
                  <p className="text-slate-400">GEMINI_API_KEY=<span className="text-violet-400">your_key</span></p>
                  <p className="text-slate-400">QDRANT_URL=<span className="text-violet-400">http://localhost:6333</span></p>
                </div>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-slate-800">
              <h4 className="font-medium mb-3 flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-xs">3</span>Запуск</h4>
              <div className="bg-slate-950 rounded-lg p-4 font-mono text-sm inline-block"><p className="text-emerald-400">python agent.py</p></div>
            </div>
          </CardContent>
        </Card>
      </section>

      <footer className="border-t border-slate-800 py-8 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-slate-500 text-sm mb-2">Vika_Ok v8.3 — Персональный AI-агент с умным роутингом</p>
          <p className="text-slate-600 text-xs">Хозяин: Вячеслав (БАС) · ЗСУ</p>
          <div className="flex justify-center gap-4 mt-4">
            <a href="https://github.com/Redrock453/vika_ok" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition-colors"><Github className="w-5 h-5" /></a>
          </div>
        </div>
      </footer>
    </div>
  )
}