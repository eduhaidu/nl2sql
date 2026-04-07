'use client';
import { redirect } from "next/dist/server/api-utils";
import { useState } from "react";
import { useRouter } from "next/navigation";


export default function Home() {
    const router = useRouter();
    return (
        <main className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="max-w-2xl text-center">
          <h1 className="text-5xl font-bold mb-6 text-white">
            Welcome to NL2SQL
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            Transform natural language into SQL queries with AI
          </p>
          
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 mb-8">
            <button
              onClick={() => router.push("/auth/login")}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors text-lg"
            >
              Get Started
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="text-3xl mb-2">💬</div>
              <h3 className="font-semibold text-white mb-2">Natural Language</h3>
              <p className="text-sm text-gray-400">
                Ask questions in plain English, no SQL knowledge required
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="text-3xl mb-2">🔄</div>
              <h3 className="font-semibold text-white mb-2">Smart Retry</h3>
              <p className="text-sm text-gray-400">
                Refine queries automatically when results aren't what you expect
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="text-3xl mb-2">💾</div>
              <h3 className="font-semibold text-white mb-2">Conversations</h3>
              <p className="text-sm text-gray-400">
                All your queries saved per database connection
              </p>
            </div>
          </div>
        </div>
      </main>
    )
}