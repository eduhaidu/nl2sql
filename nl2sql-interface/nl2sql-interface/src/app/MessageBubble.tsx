'use client';

export default function MessageBubble({ message, isUser}: {message: string; isUser: boolean}){
    return (
        <div className={`max-w-xl p-4 rounded-lg shadow-md mb-4 ${isUser ? 'bg-blue-500 text-white self-end' : 'bg-gray-200 text-gray-800 self-start'}`}>
            {message}
        </div>
    )
}