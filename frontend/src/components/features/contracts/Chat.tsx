import { ChatProvider } from "./provider";
import { ChatInput } from "./input";
import { ChatOutput } from "./output";

export function Chat() {
    return (
        <ChatProvider>
            <div className="flex flex-col h-full gap-4">
                <ChatOutput />
                <ChatInput />
            </div>
        </ChatProvider>
    );
}