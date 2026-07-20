import { Message } from "../types";
import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "flex max-w-[80%] md:max-w-[70%] gap-3 p-4 rounded-xl",
          isUser
            ? "bg-primary text-primary-foreground flex-row-reverse"
            : "bg-muted"
        )}
      >
        <div className="flex-shrink-0 mt-1">
          {isUser ? (
            <div className="bg-primary-foreground/20 rounded-full p-1">
              <User className="h-5 w-5" />
            </div>
          ) : (
            <div className="bg-background rounded-full p-1 border">
              <Bot className="h-5 w-5" />
            </div>
          )}
        </div>
        
        <div className={cn("prose prose-sm break-words", isUser && "text-primary-foreground")}>
          {message.content}
        </div>
      </div>
    </div>
  );
}
