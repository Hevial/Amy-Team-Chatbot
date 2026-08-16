import * as React from "react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import { askQuestion, type QueryResponse } from "./lib/api"
import {
  MessageScrollerProvider,
  MessageScroller,
  MessageScrollerViewport,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerButton
} from "./components/ui/message-scroller"
import { Message, MessageContent, MessageGroup } from "./components/ui/message"
import { Bubble, BubbleContent } from "./components/ui/bubble"
import { Textarea } from "./components/ui/textarea"
import { Button } from "./components/ui/button"
import { SendHorizontal, Sparkles, FileText, Lightbulb, Moon, Sun, Plus, Globe, Brain } from "lucide-react"
import { AmyLogo } from "./components/AmyLogo"

type ChatMessage = {
  id: string
  role: "user" | "bot"
  content: string
  isTyping?: boolean
  sources?: QueryResponse["sources"]
}

const SUGGESTIONS = [
  { icon: <Sparkles className="size-4" />, text: "What is the overall strategy?" },
  { icon: <FileText className="size-4" />, text: "Summarize the latest patch notes." },
  { icon: <Lightbulb className="size-4" />, text: "How can we improve our mid-game?" },
]

export function App() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = React.useState("")
  const [isPending, setIsPending] = React.useState(false)
  const [theme, setTheme] = React.useState<"light" | "dark">("dark")
  const [enableGoogleSearch, setEnableGoogleSearch] = React.useState(false)
  const [enableDeepSearch, setEnableDeepSearch] = React.useState(false)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [theme])

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages])

  const handleResetChat = () => {
    setMessages([])
  }

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark")
  }

  const handleSend = async (content: string) => {
    if (!content.trim() || isPending) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsPending(true)

    try {
      const typingId = (Date.now() + 1).toString()
      setMessages((prev) => [
        ...prev,
        { id: typingId, role: "bot", content: "", isTyping: true },
      ])

      const response = await askQuestion({
        question: content.trim(),
        enable_google_search: enableGoogleSearch,
        top_k: enableDeepSearch ? 15 : undefined
      })

      setMessages((prev) =>
        prev.map((m) =>
          m.id === typingId
            ? { ...m, content: response.answer, isTyping: false, sources: response.sources }
            : m
        )
      )
    } catch (error: any) {
      setMessages((prev) => {
        const newMessages = [...prev]
        const last = newMessages[newMessages.length - 1]
        if (last && last.isTyping) {
          last.content = `Error: ${error.message || "Failed to fetch response."}`
          last.isTyping = false
        }
        return newMessages
      })
    } finally {
      setIsPending(false)
    }
  }

  const handleSubmit = (e?: React.SyntheticEvent) => {
    e?.preventDefault()
    handleSend(inputValue)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex h-dvh w-full flex-col bg-background font-sans selection:bg-primary/20 relative">
      {messages.length > 0 && (
        <header className="absolute top-6 left-8 flex items-center gap-2.5 pointer-events-none z-50 animate-in fade-in duration-500">
          <AmyLogo className="size-8 text-chart-4" />
        </header>
      )}

      <div className="absolute top-6 right-8 z-50 flex items-center gap-2 animate-in fade-in duration-500">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="rounded-full text-muted-foreground hover:text-foreground transition-all"
          title="Toggle Theme"
        >
          {theme === "dark" ? (
            <Sun className="size-5 animate-in zoom-in-50 spin-in-90 duration-300" />
          ) : (
            <Moon className="size-5 animate-in zoom-in-50 -spin-in-90 duration-300" />
          )}
        </Button>
        <Button
          variant="default"
          onClick={handleResetChat}
          className="rounded-full shadow-sm gap-1.5 px-4 h-10 font-medium"
        >
          <Plus className="size-4" />
          New Chat
        </Button>
      </div>

      <main className="flex min-h-0 flex-1 flex-col items-center w-full">
        {messages.length === 0 ? (
          <div className="relative flex flex-1 flex-col items-center justify-center w-full max-w-3xl gap-8 px-4 animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out pt-18">
            <div className="pointer-events-none absolute bottom-1/3 left-1/2 -translate-x-1/2 w-full max-w-3xl h-64 bg-chart-3/20 blur-[125px] rounded-[100%]" />

            <div className="flex flex-col items-center gap-4 text-center">
              <AmyLogo className="size-16" />
              <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-linear-to-r from-primary via-chart-2 to-primary bg-clip-text text-transparent animate-gradient-text drop-shadow-sm pb-1">
                Hi, I'm Amy
              </h1>
              <p className="text-muted-foreground text-lg max-w-md">
                Your AI Assistant Coach. How can I help you and the team today?
              </p>
            </div>

            <div className="flex flex-wrap justify-center gap-3 w-full max-w-2xl mt-4">
              {SUGGESTIONS.map((s, i) => (
                <Button
                  key={i}
                  onClick={() => handleSend(s.text)}
                  variant={"outline"}
                  size="2xl"
                >
                  {s.icon}
                  {s.text}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <MessageScrollerProvider>
            <MessageScroller className="w-full flex-1">
              <MessageScrollerViewport>
                <MessageScrollerContent className="w-full max-w-3xl mx-auto px-4 pb-8 pt-20">
                  <MessageGroup>
                    {messages.map((message) => (
                      <MessageScrollerItem key={message.id}>
                        <Message align={message.role === "user" ? "end" : "start"} className="mb-6">
                          <MessageContent className={message.role === "user" ? "" : "w-full max-w-full"}>
                            {message.isTyping ? (
                              <div className="flex w-full items-center gap-3 py-2 mt-2">
                                <AmyLogo className="size-5 animate-pulse text-chart-4" />
                                <span className="text-sm font-medium text-muted-foreground animate-pulse tracking-wide">
                                  Thinking...
                                </span>
                              </div>
                            ) : message.role === "user" ? (
                              <Bubble variant="default" className="max-w-[80%] rounded-2xl">
                                <BubbleContent className="px-5 py-3 text-[15px]">{message.content}</BubbleContent>
                              </Bubble>
                            ) : (
                              <Bubble variant="ghost" className="w-full max-w-full">
                                <BubbleContent className="w-full max-w-full">
                                  <div className="prose prose-sm md:prose-base dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 max-w-none text-foreground w-full">
                                    <ReactMarkdown
                                      remarkPlugins={[remarkGfm, remarkMath]}
                                      rehypePlugins={[rehypeKatex]}
                                    >
                                      {message.content}
                                    </ReactMarkdown>
                                  </div>
                                  {message.sources && message.sources.length > 0 && (
                                    <div className="mt-4 flex flex-wrap gap-2">
                                      {message.sources.map((s, i) => (
                                        <span key={i} className="text-xs bg-muted/50 text-muted-foreground px-2 py-1 rounded-md border border-border/50">
                                          {s.title || s.file_name || "Source"}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </BubbleContent>
                              </Bubble>
                            )}
                          </MessageContent>
                        </Message>
                      </MessageScrollerItem>
                    ))}
                    <div ref={messagesEndRef} className="h-px w-full" />
                  </MessageGroup>
                </MessageScrollerContent>
              </MessageScrollerViewport>
              <MessageScrollerButton />
            </MessageScroller>
          </MessageScrollerProvider>
        )}

        <div className="w-full max-w-3xl shrink-0 px-4 pb-6 pt-2">
          <form
            onSubmit={handleSubmit}
            className="relative flex w-full flex-col gap-2 rounded-3xl border bg-card p-2 shadow-sm focus-within:ring-1 focus-within:ring-ring"
          >
            <Textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Amy anything..."
              className="min-h-13 w-full resize-none border-0 bg-transparent px-4 py-3.5 focus-visible:ring-0 max-h-48 scrollbar-none text-base"
              rows={1}
            />
            <div className="flex items-center justify-between px-2 pb-1">
              <div className="flex items-center gap-1 text-muted-foreground pl-1">
                <Button 
                  type="button"
                  variant={enableGoogleSearch ? "outline" : "ghost"} 
                  size="sm" 
                  onClick={() => setEnableGoogleSearch(!enableGoogleSearch)}
                  className={`rounded-full gap-2 text-[13px] h-8 px-3 transition-all ${enableGoogleSearch
                    ? 'border-chart-3/40 bg-chart-3/10 text-chart-3 hover:bg-chart-3/20 hover:text-chart-3'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  <Globe className="size-4" />
                  Web Search
                </Button>
                <Button 
                  type="button"
                  variant={enableDeepSearch ? "outline" : "ghost"} 
                  size="sm" 
                  onClick={() => setEnableDeepSearch(!enableDeepSearch)}
                  className={`rounded-full gap-2 text-[13px] h-8 px-3 transition-all ${enableDeepSearch
                    ? 'border-chart-3/40 bg-chart-3/10 text-chart-3 hover:bg-chart-3/20 hover:text-chart-3'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  <Brain className="size-4" />
                  Deep Search
                </Button>
              </div>
              <Button
                type="submit"
                size="icon"
                disabled={!inputValue.trim() || isPending}
                className="size-9 shrink-0 rounded-full"
              >
                <SendHorizontal className="size-4" />
                <span className="sr-only">Send message</span>
              </Button>
            </div>
          </form>
          <div className="mt-3 text-center text-xs text-muted-foreground/75">
            Amy can make mistakes. Consider verifying critical information.
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
