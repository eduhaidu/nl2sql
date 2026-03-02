'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useRouter, usePathname } from 'next/navigation';

interface Conversation {
  id: string;
  name: string | null;
  created_at: string;
}

interface SidebarProps {
  onNewChat: () => void;
}

export default function Sidebar({ onNewChat }: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEditOptions, setShowEditOptions] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const fetchConversations = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/conversations');
      setConversations(response.data.conversations.map((conv: any) => ({
        id: conv[0],
        name: conv[1],
        created_at: conv[2]
      })));
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    if (!confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
      return;
    }
    try{
      await axios.delete(`http://127.0.0.1:8000/conversations/${conversationId}`);
      fetchConversations();
      // If the deleted conversation is currently open, navigate back to home
      if (pathname === `/conversations/${conversationId}`) {
        router.push('/');
      }
    }
    catch(error){
      console.error('Error deleting conversation:', error);
      alert('Failed to delete conversation. Please try again.');
    }
  }

  const handleRenameConversation = async (conversationId: string) => {
    const newName = prompt('Enter a new name for this conversation:');
    if (!newName) {
      return;
    }
    try {
      await axios.put(`http://127.0.0.1:8000/conversations/${conversationId}`, { name: newName });
      fetchConversations();
    } catch (error) {
      console.error('Error renaming conversation:', error);
      alert('Failed to rename conversation. Please try again.');
    }
  }

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
              <div key={conv.id}>
                <div className="flex items-start gap-1">
                  <button
                    onClick={() => router.push(`/conversations/${conv.id}`)}
                    className={`flex-1 text-left px-3 py-2 rounded-lg transition-colors ${
                      currentConversationId === conv.id
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <div className="text-sm truncate">
                      {conv.name ? conv.name : `Conversation ${conv.id.substring(0, 8)}`}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatDate(conv.created_at)}
                    </div>
                  </button>
                  <button 
                    onClick={(e)=>{e.stopPropagation(); setShowEditOptions(showEditOptions === conv.id ? null : conv.id)}} 
                    className={`px-2 py-2 text-gray-500 hover:text-white rounded-lg transition-colors ${
                      showEditOptions === conv.id ? 'bg-gray-800' : 'hover:bg-gray-800'
                    }`}
                  >
                    ⋮ 
                  </button>
                </div>
                {showEditOptions === conv.id && (
                  <div className="ml-4 mt-1 flex gap-2 pb-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleRenameConversation(conv.id); setShowEditOptions(null); }}
                      className="text-xs text-gray-400 hover:text-white transition-colors"
                    >
                      Rename
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteConversation(conv.id); setShowEditOptions(null); }}
                      className="text-xs text-red-400 hover:text-red-300 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
