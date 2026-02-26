'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useRouter, usePathname } from 'next/navigation';

interface Conversation {
  id: string;
  created_at: string;
}

interface SidebarProps {
  onNewChat: () => void;
}

export default function Sidebar({ onNewChat }: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchConversations = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/conversations');
      setConversations(response.data.conversations.map((conv: any) => ({
        id: conv[0],
        created_at: conv[1]
      })));
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const getCurrentConversationId = () => {
    const match = pathname.match(/\/conversations\/([^/]+)/);
    return match ? match[1] : null;
  };

  const currentConversationId = getCurrentConversationId();

  return (
    <aside className="w-64 bg-gray-900 h-screen flex flex-col border-r border-gray-800">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <button
          onClick={onNewChat}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          <span className="text-xl">+</span>
          New Chat
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="text-gray-500 text-center py-4">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="text-gray-500 text-center py-8 px-4 text-sm">
            No conversations yet. Start by importing a database!
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => router.push(`/conversations/${conv.id}`)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  currentConversationId === conv.id
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm truncate flex-1">
                    Conversation
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {formatDate(conv.created_at)}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
