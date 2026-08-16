import * as React from "react"
import ReactMarkdown from 'react-markdown'
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
import { SendHorizontal, Sparkles, FileText, Lightbulb } from "lucide-react"
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
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages])

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

      const response = await askQuestion({ question: userMessage.content })

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

  const handleSubmit = (e?: React.FormEvent) => {
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
    <div className="flex h-dvh w-full flex-col bg-background font-sans selection:bg-primary/20">
      <main className="flex min-h-0 flex-1 flex-col items-center">
        {messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center w-full max-w-3xl gap-8 px-4 animate-in fade-in zoom-in duration-500">
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
                <button
                  key={i}
                  onClick={() => handleSend(s.text)}
                  className="flex items-center gap-2 rounded-2xl border bg-card px-4 py-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-[0.98]"
                >
                  {s.icon}
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <MessageScrollerProvider>
            <MessageScroller className="w-full flex-1">
              <MessageScrollerViewport>
                <MessageScrollerContent className="w-full max-w-3xl mx-auto px-4 py-8">
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
                                    <ReactMarkdown>{message.content}</ReactMarkdown>
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
              <div className="flex items-center gap-2 text-muted-foreground">
                {/* Optional attachments/tools buttons can go here */}
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
