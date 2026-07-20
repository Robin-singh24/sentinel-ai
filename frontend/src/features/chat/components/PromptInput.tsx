import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PromptInputProps {
  onSend: (content: string) => void;
  isSending: boolean;
  disabled?: boolean;
}

export function PromptInput({ onSend, isSending, disabled }: PromptInputProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (content.trim() && !isSending && !disabled) {
      onSend(content.trim());
      setContent("");
      
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    
    // Auto-resize
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  useEffect(() => {
    if (!isSending && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isSending]);

  return (
    <div className="relative border rounded-lg bg-background shadow-sm focus-within:ring-1 focus-within:ring-primary overflow-hidden">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (Shift+Enter for newline)"
        className="w-full resize-none bg-transparent p-4 pr-12 focus:outline-none min-h-[60px] max-h-[200px]"
        disabled={isSending || disabled}
        rows={1}
      />
      <Button
        size="icon"
        className="absolute right-2 bottom-2 h-8 w-8 rounded-md"
        onClick={handleSend}
        disabled={!content.trim() || isSending || disabled}
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
