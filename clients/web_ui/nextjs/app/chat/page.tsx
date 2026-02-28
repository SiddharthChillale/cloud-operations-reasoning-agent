"use client";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">
            Select a session from the sidebar or start a new chat
          </p>
        </div>
      </div>
    </div>
  );
}
