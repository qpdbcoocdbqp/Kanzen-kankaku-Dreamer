import { useState } from "react";
import { useFrontendTool, useCoAgent } from "@copilotkit/react-core";
import { AgentState } from "@/lib/types";

// TypeScript interfaces for component props and state
export interface HRFAQComponentProps {
  themeColor: string;
  onModeChange?: (mode: 'hr' | 'general') => void;
  // Remove local state management in favor of shared agent state
  agentState?: AgentState;
  setAgentState?: (state: AgentState) => void;
}

// Mode switching interface
export interface ModeSwitchingState {
  currentMode: 'hr' | 'general';
  previousMode: 'hr' | 'general';
  transitionInProgress: boolean;
  contextPreserved: boolean;
}

export interface HRFAQState {
  currentMode: 'greeting' | 'conversation';
  lastAnswer: string | null;
  followUpQuestions: string[];
  conversationHistory: Array<{
    question: string;
    answer: string;
    timestamp: Date;
  }>;
}

export interface QuestionButtonProps {
  question: string;
  onClick: (question: string) => void;
  variant: 'primary' | 'secondary';
  className?: string;
}

export interface FollowUpSuggestionsProps {
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
  maxSuggestions: number;
}

// HR Question Category interface for categorization system
export interface HRQuestionCategory {
  id: string;
  title: string;
  questions: string[];
  keywords: string[];
}

// Main HR FAQ Component
export function HRFAQComponent({ themeColor, onModeChange, agentState, setAgentState }: HRFAQComponentProps) {
  // Use shared agent state instead of local state
  const { state, setState } = useCoAgent<AgentState>({
    name: "my_agent",
    initialState: {
      proverbs: [],
      hrMode: false,
      currentCategory: null,
      greetingQuestions: [],
      followUpSuggestions: [],
      conversationHistory: [],
    },
  });

  // Mode switching state management
  const [modeSwitchingState, setModeSwitchingState] = useState<ModeSwitchingState>({
    currentMode: state.hrMode ? 'hr' : 'general',
    previousMode: 'general',
    transitionInProgress: false,
    contextPreserved: true
  });

  // Local UI state for component-specific behavior
  const [localState, setLocalState] = useState<HRFAQState>({
    currentMode: state.hrMode ? 'conversation' : 'greeting',
    lastAnswer: null,
    followUpQuestions: state.followUpSuggestions || [],
    conversationHistory: (state.conversationHistory || []).map(entry => ({
      question: entry.question,
      answer: entry.answer,
      timestamp: new Date(entry.timestamp)
    }))
  });

  // Mode switching functionality - toggle between HR FAQ and general agent modes
  const switchToHRMode = async () => {
    try {
      setModeSwitchingState(prev => ({
        ...prev,
        transitionInProgress: true,
        previousMode: prev.currentMode
      }));

      // Preserve current context before switching
      const currentContext = {
        conversationHistory: localState.conversationHistory,
        followUpQuestions: localState.followUpQuestions,
        lastAnswer: localState.lastAnswer,
        agentState: state
      };

      // Store context in localStorage
      const contextKey = 'hr-faq-context-general';
      localStorage.setItem(contextKey, JSON.stringify({
        data: currentContext,
        timestamp: new Date().toISOString(),
        preserved: true
      }));

      // Update shared agent state to HR mode
      setState({
        ...state,
        hrMode: true,
        currentCategory: state.currentCategory || null
      });

      // Try to restore HR context if available
      const hrContextKey = 'hr-faq-context-hr';
      const storedHRContext = localStorage.getItem(hrContextKey);
      
      if (storedHRContext) {
        try {
          const parsedContext = JSON.parse(storedHRContext);
          if (parsedContext.preserved && parsedContext.data) {
            // Restore HR conversation history
            if (parsedContext.data.conversationHistory) {
              setLocalState(prev => ({
                ...prev,
                conversationHistory: parsedContext.data.conversationHistory,
                currentMode: parsedContext.data.conversationHistory.length > 0 ? 'conversation' : 'greeting'
              }));
            }
            
            // Restore follow-up suggestions
            if (parsedContext.data.followUpQuestions) {
              setLocalState(prev => ({
                ...prev,
                followUpQuestions: parsedContext.data.followUpQuestions
              }));
            }
          }
        } catch (error) {
          console.error('Error restoring HR context:', error);
        }
      } else {
        // No previous HR context, start fresh
        setLocalState(prev => ({
          ...prev,
          currentMode: state.conversationHistory && state.conversationHistory.length > 0 ? 'conversation' : 'greeting'
        }));
      }

      // Update mode switching state
      setModeSwitchingState(prev => ({
        ...prev,
        currentMode: 'hr',
        transitionInProgress: false,
        contextPreserved: true
      }));

      // Notify parent component
      if (onModeChange) {
        onModeChange('hr');
      }

      console.log('Switched to HR mode successfully with context preservation');
    } catch (error) {
      console.error('Error switching to HR mode:', error);
      setModeSwitchingState(prev => ({
        ...prev,
        transitionInProgress: false
      }));
    }
  };

  const switchToGeneralMode = async () => {
    try {
      setModeSwitchingState(prev => ({
        ...prev,
        transitionInProgress: true,
        previousMode: prev.currentMode
      }));

      // Preserve current HR context before switching
      const currentHRContext = {
        conversationHistory: localState.conversationHistory,
        followUpQuestions: localState.followUpQuestions,
        lastAnswer: localState.lastAnswer,
        agentState: state
      };

      // Store HR context in localStorage
      const hrContextKey = 'hr-faq-context-hr';
      localStorage.setItem(hrContextKey, JSON.stringify({
        data: currentHRContext,
        timestamp: new Date().toISOString(),
        preserved: true
      }));

      // Update shared agent state to general mode
      setState({
        ...state,
        hrMode: false
        // Keep conversation history and other HR state for context preservation
      });

      // Try to restore general context if available
      const generalContextKey = 'hr-faq-context-general';
      const storedGeneralContext = localStorage.getItem(generalContextKey);
      
      if (storedGeneralContext) {
        try {
          const parsedContext = JSON.parse(storedGeneralContext);
          if (parsedContext.preserved && parsedContext.data) {
            // Restore general conversation state if needed
            if (parsedContext.data.conversationHistory) {
              setLocalState(prev => ({
                ...prev,
                conversationHistory: parsedContext.data.conversationHistory,
                currentMode: 'greeting'
              }));
            }
          }
        } catch (error) {
          console.error('Error restoring general context:', error);
        }
      } else {
        // No previous general context, reset to greeting
        setLocalState(prev => ({
          ...prev,
          currentMode: 'greeting'
        }));
      }

      // Update mode switching state
      setModeSwitchingState(prev => ({
        ...prev,
        currentMode: 'general',
        transitionInProgress: false,
        contextPreserved: true
      }));

      // Notify parent component
      if (onModeChange) {
        onModeChange('general');
      }

      console.log('Switched to general mode successfully with context preservation');
    } catch (error) {
      console.error('Error switching to general mode:', error);
      setModeSwitchingState(prev => ({
        ...prev,
        transitionInProgress: false
      }));
    }
  };

  // Generic mode toggle function for smooth transitions
  const toggleMode = async () => {
    if (modeSwitchingState.transitionInProgress) {
      console.log('Mode transition already in progress');
      return;
    }

    if (modeSwitchingState.currentMode === 'hr') {
      await switchToGeneralMode();
    } else {
      await switchToHRMode();
    }
  };

  // Function to process questions through agent system
  const submitQuestionToAgent = async (question: string) => {
    try {
      // Automatically switch to HR mode when submitting HR questions
      if (modeSwitchingState.currentMode !== 'hr') {
        await switchToHRMode();
      }

      // Update state to show question is being processed
      const processingEntry = {
        question: question,
        answer: "正在處理您的問題...",
        category: determineCategoryFromQuestion(question),
        timestamp: new Date().toISOString()
      };

      // Update shared agent state
      setState({
        ...state,
        hrMode: true,
        currentCategory: determineCategoryFromQuestion(question),
        conversationHistory: [
          ...(state.conversationHistory || []),
          processingEntry
        ]
      });

      // Update local state for UI
      setLocalState(prevState => ({
        ...prevState,
        currentMode: 'conversation',
        conversationHistory: [
          ...prevState.conversationHistory,
          {
            question: question,
            answer: "正在處理您的問題...",
            timestamp: new Date()
          }
        ]
      }));

      // The actual agent processing will be handled by the backend
      // This frontend tool will trigger the agent to process the question
      console.log('Question submitted to agent:', question);
      
      return true;
    } catch (error) {
      console.error('Error submitting question to agent:', error);
      
      // Update state with error message
      const errorEntry = {
        question: question,
        answer: "抱歉，處理您的問題時發生錯誤。請稍後再試。",
        category: determineCategoryFromQuestion(question),
        timestamp: new Date().toISOString()
      };

      setState({
        ...state,
        conversationHistory: [
          ...(state.conversationHistory || []),
          errorEntry
        ]
      });

      setLocalState(prevState => ({
        ...prevState,
        conversationHistory: [
          ...prevState.conversationHistory,
          {
            question: question,
            answer: "抱歉，處理您的問題時發生錯誤。請稍後再試。",
            timestamp: new Date()
          }
        ]
      }));

      return false;
    }
  };

  // Frontend tool to generate follow-up suggestions
  useFrontendTool({
    name: "generateFollowUpSuggestions",
    parameters: [
      {
        name: "question",
        description: "The original question that was asked",
        required: true,
      },
      {
        name: "answer",
        description: "The agent's response to the question",
        required: true,
      },
    ],
    handler: ({ question, answer }) => {
      // This will trigger the backend to generate follow-up suggestions
      // The backend will call generate_follow_up_questions and update the state
      console.log('Generating follow-up suggestions for:', question);
    },
  });

  // Enhanced frontend tool to handle HR question submission with proper agent integration
  useFrontendTool({
    name: "submitHRQuestion",
    parameters: [
      {
        name: "question",
        description: "The HR question to submit to the agent for processing",
        required: true,
      },
    ],
    handler: async ({ question }) => {
      // This tool will be called by the frontend and should trigger the agent
      // The agent will process the question and provide a response
      console.log('HR Question submitted via frontend tool:', question);
      
      // Update local state to show the question is being processed
      setLocalState(prevState => ({
        ...prevState,
        currentMode: 'conversation',
        conversationHistory: [
          ...prevState.conversationHistory,
          {
            question: question,
            answer: "正在處理您的問題...",
            timestamp: new Date()
          }
        ]
      }));

      // The actual processing will be handled by the agent backend
      // This frontend tool serves as a bridge to trigger agent processing
      return { status: "submitted", question: question };
    },
  });

  // Frontend tool to handle mode switching with context preservation
  useFrontendTool({
    name: "switchAgentMode",
    parameters: [
      {
        name: "targetMode",
        description: "The mode to switch to: 'hr' or 'general'",
        required: true,
      },
      {
        name: "preserveContext",
        description: "Whether to preserve conversation context during switch",
        required: false,
      },
    ],
    handler: async ({ targetMode, preserveContext = true }) => {
      try {
        if (targetMode === 'hr') {
          await switchToHRMode();
        } else {
          await switchToGeneralMode();
        }
        
        console.log(`Mode switched to ${targetMode} with context preservation: ${preserveContext}`);
      } catch (error) {
        console.error('Error in mode switch frontend tool:', error);
      }
    },
  });

  // Frontend tool to preserve conversation context
  useFrontendTool({
    name: "preserveConversationContext",
    parameters: [
      {
        name: "mode",
        description: "The mode context is being preserved for",
        required: true,
      },
      {
        name: "contextData",
        description: "The context data to preserve",
        required: true,
      },
    ],
    handler: ({ mode, contextData }) => {
      try {
        // Store context in local storage as backup
        const contextKey = `hr-faq-context-${mode}`;
        localStorage.setItem(contextKey, JSON.stringify({
          data: contextData,
          timestamp: new Date().toISOString(),
          preserved: true
        }));
        
        console.log(`Context preserved for ${mode} mode`);
      } catch (error) {
        console.error('Error preserving context:', error);
      }
    },
  });

  // Frontend tool to restore conversation context
  useFrontendTool({
    name: "restoreConversationContext",
    parameters: [
      {
        name: "mode",
        description: "The mode to restore context for",
        required: true,
      },
    ],
    handler: ({ mode }) => {
      try {
        const contextKey = `hr-faq-context-${mode}`;
        const storedContext = localStorage.getItem(contextKey);
        
        if (storedContext) {
          const parsedContext = JSON.parse(storedContext);
          
          if (parsedContext.preserved && parsedContext.data) {
            // Restore conversation history if available
            if (parsedContext.data.conversationHistory) {
              setLocalState(prev => ({
                ...prev,
                conversationHistory: parsedContext.data.conversationHistory.map((entry: any) => ({
                  question: entry.question,
                  answer: entry.answer,
                  timestamp: new Date(entry.timestamp)
                }))
              }));
            }
            
            // Restore follow-up suggestions if available
            if (parsedContext.data.followUpSuggestions) {
              setLocalState(prev => ({
                ...prev,
                followUpQuestions: parsedContext.data.followUpSuggestions
              }));
            }
            
            console.log(`Context restored for ${mode} mode`);
            return { status: "success", context: parsedContext.data };
          }
        }
        
        console.log(`No preserved context found for ${mode} mode`);
        return { status: "success", context: {} };
      } catch (error) {
        console.error('Error restoring context:', error);
        return { status: "error", context: {} };
      }
    },
  });

  // Frontend tool to update conversation with agent response
  useFrontendTool({
    name: "updateHRAnswer",
    parameters: [
      {
        name: "question",
        description: "The original question that was asked",
        required: true,
      },
      {
        name: "answer",
        description: "The agent's response to the HR question",
        required: true,
      },
      {
        name: "followUpSuggestions",
        description: "Array of follow-up question suggestions",
        required: false,
      },
    ],
    handler: ({ question, answer, followUpSuggestions }) => {
      // Ensure followUpSuggestions is an array
      const suggestions = Array.isArray(followUpSuggestions) ? followUpSuggestions : [];
      
      // Update the conversation history with the agent's response
      const updatedHistory = (state.conversationHistory || []).map(entry => 
        entry.question === question && entry.answer === "正在處理您的問題..." 
          ? { ...entry, answer: answer }
          : entry
      );

      // Update shared agent state with response and follow-ups
      setState({
        ...state,
        conversationHistory: updatedHistory,
        followUpSuggestions: suggestions.slice(0, 2) as string[] // Limit to 2 as per requirements
      });

      // Update local state for UI
      const updatedLocalHistory = localState.conversationHistory.map(entry =>
        entry.question === question && entry.answer === "正在處理您的問題..."
          ? { ...entry, answer: answer }
          : entry
      );

      setLocalState(prevState => ({
        ...prevState,
        conversationHistory: updatedLocalHistory,
        followUpQuestions: suggestions.slice(0, 2) as string[],
        lastAnswer: answer
      }));
    },
  });

  // Question button click handler - populates input field and preserves Chinese text
  const handleQuestionClick = async (question: string) => {
    try {
      // Ensure Chinese text preservation by maintaining original encoding
      const preservedQuestion = question.trim();
      
      // Automatically switch to HR mode when clicking HR questions
      if (modeSwitchingState.currentMode !== 'hr') {
        await switchToHRMode();
      }

      // Try to find and populate the chat input field
      const chatInput = document.querySelector('textarea[placeholder*="message"], input[placeholder*="message"], textarea[data-testid="copilot-input"], input[data-testid="copilot-input"]') as HTMLTextAreaElement | HTMLInputElement;
      
      if (chatInput) {
        // Set the value and trigger input events
        chatInput.value = preservedQuestion;
        chatInput.dispatchEvent(new Event('input', { bubbles: true }));
        chatInput.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Focus the input field
        chatInput.focus();
        
        // Try to trigger form submission or send button click
        setTimeout(() => {
          const sendButton = document.querySelector('button[type="submit"], button[aria-label*="send"], button[data-testid="send-button"]') as HTMLButtonElement;
          if (sendButton) {
            sendButton.click();
          } else {
            // Try to trigger Enter key press
            const enterEvent = new KeyboardEvent('keydown', {
              key: 'Enter',
              code: 'Enter',
              keyCode: 13,
              which: 13,
              bubbles: true
            });
            chatInput.dispatchEvent(enterEvent);
          }
        }, 100);
        
        console.log('Question populated in chat input:', preservedQuestion);
      } else {
        console.warn('Chat input field not found, falling back to frontend tool');
        // Fallback to frontend tool
        await submitQuestionToAgent(preservedQuestion);
      }
    } catch (error) {
      console.error('Error handling question click:', error);
      // Fallback to frontend tool
      await submitQuestionToAgent(question.trim());
    }
  };

  // Helper function to determine category from question
  const determineCategoryFromQuestion = (question: string): string => {
    const categories = Object.values(HR_QUESTION_CATEGORIES);
    
    for (const category of categories) {
      if (category.questions.includes(question)) {
        return category.id;
      }
      // Check if question contains category keywords
      if (category.keywords.some(keyword => question.includes(keyword))) {
        return category.id;
      }
    }
    
    return 'general'; // Default category
  };

  // Follow-up question click handler
  const handleFollowUpClick = async (followUpQuestion: string) => {
    try {
      const preservedQuestion = followUpQuestion.trim();
      
      // Try to find and populate the chat input field
      const chatInput = document.querySelector('textarea[placeholder*="message"], input[placeholder*="message"], textarea[data-testid="copilot-input"], input[data-testid="copilot-input"]') as HTMLTextAreaElement | HTMLInputElement;
      
      if (chatInput) {
        // Set the value and trigger input events
        chatInput.value = preservedQuestion;
        chatInput.dispatchEvent(new Event('input', { bubbles: true }));
        chatInput.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Focus the input field
        chatInput.focus();
        
        // Try to trigger form submission or send button click
        setTimeout(() => {
          const sendButton = document.querySelector('button[type="submit"], button[aria-label*="send"], button[data-testid="send-button"]') as HTMLButtonElement;
          if (sendButton) {
            sendButton.click();
          } else {
            // Try to trigger Enter key press
            const enterEvent = new KeyboardEvent('keydown', {
              key: 'Enter',
              code: 'Enter',
              keyCode: 13,
              which: 13,
              bubbles: true
            });
            chatInput.dispatchEvent(enterEvent);
          }
        }, 100);
        
        console.log('Follow-up question populated in chat input:', preservedQuestion);
      } else {
        console.warn('Chat input field not found, falling back to frontend tool');
        // Fallback to frontend tool
        await submitQuestionToAgent(preservedQuestion);
      }
    } catch (error) {
      console.error('Error handling follow-up click:', error);
      // Fallback to frontend tool
      await submitQuestionToAgent(followUpQuestion.trim());
    }
  };

  // HR Question Categories and Data - implementing proper categorization system
  const HR_QUESTION_CATEGORIES = {
    benefits: {
      id: 'benefits',
      title: '福利相關',
      questions: [
        '我的年假還剩多少天？',
        '公司的健康保險包含哪些項目？',
        '退休金計劃是如何運作的？'
      ],
      keywords: ['年假', '保險', '退休金', '福利']
    },
    policies: {
      id: 'policies',
      title: '政策規定',
      questions: [
        '遠距工作的政策是什麼？',
        '請假流程該如何進行？',
        '加班費是如何計算的？'
      ],
      keywords: ['遠距', '請假', '加班', '政策']
    },
    career: {
      id: 'career',
      title: '職涯發展',
      questions: [
        '如何申請內部轉職？',
        '公司有哪些培訓課程？',
        '績效評估的標準是什麼？'
      ],
      keywords: ['轉職', '培訓', '績效', '發展']
    }
  };

  // Extract three common HR questions (one from each category) for greeting page
  const greetingQuestions = [
    HR_QUESTION_CATEGORIES.benefits.questions[0],  // 我的年假還剩多少天？
    HR_QUESTION_CATEGORIES.benefits.questions[1],  // 公司的健康保險包含哪些項目？
    HR_QUESTION_CATEGORIES.policies.questions[0]   // 遠距工作的政策是什麼？
  ];

  return (
    <div 
      className="bg-white/20 backdrop-blur-md p-8 rounded-2xl shadow-xl max-w-2xl w-full"
      style={{ 
        borderColor: themeColor,
        borderWidth: '2px',
        borderStyle: 'solid',
        // Ensure proper Chinese text rendering at container level
        fontFamily: '"Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", system-ui, sans-serif'
      }}
      lang="zh-CN"
    >
      {/* Mode switching controls */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${modeSwitchingState.currentMode === 'hr' ? 'bg-green-400' : 'bg-gray-400'}`}></div>
          <span className="text-white/80 text-sm">
            {modeSwitchingState.currentMode === 'hr' ? 'HR模式' : '一般模式'}
          </span>
        </div>
        
        <button
          onClick={toggleMode}
          disabled={modeSwitchingState.transitionInProgress}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            modeSwitchingState.transitionInProgress 
              ? 'bg-gray-500/50 text-gray-300 cursor-not-allowed' 
              : 'bg-white/20 hover:bg-white/30 text-white hover:text-white border border-white/30 hover:border-white/50'
          }`}
        >
          {modeSwitchingState.transitionInProgress 
            ? '切換中...' 
            : modeSwitchingState.currentMode === 'hr' 
              ? '切換到一般模式' 
              : '切換到HR模式'
          }
        </button>
      </div>

      <h1 className="text-4xl font-bold text-white mb-2 text-center">
        人力資源常見問題
      </h1>
      <p className="text-gray-200 text-center italic mb-6">
        選擇常見問題或直接輸入您的問題
      </p>
      <hr className="border-white/20 my-6" />
      
      {localState.currentMode === 'greeting' && (
        <div className="flex flex-col gap-4">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold text-white mb-3">
              常見問題
            </h2>
            <p className="text-white/80 text-lg">
              請選擇以下常見問題之一，或直接在右側聊天框輸入您的問題：
            </p>
          </div>
          
          <div className="space-y-4">
            {greetingQuestions.map((question, index) => (
              <div key={index} className="w-full">
                <QuestionButton
                  question={question}
                  onClick={handleQuestionClick}
                  variant="primary"
                  className="text-lg py-4"
                />
              </div>
            ))}
          </div>
          
          <div className="mt-6 text-center">
            <p className="text-white/60 text-sm">
              點擊問題按鈕將自動填入聊天框
            </p>
          </div>
        </div>
      )}
      
      {localState.currentMode === 'conversation' && (
        <div className="flex flex-col gap-4">
          <button
            onClick={() => {
              setLocalState(prev => ({ ...prev, currentMode: 'greeting' }));
              // Don't automatically switch to general mode, just change UI state
            }}
            className="text-white/80 hover:text-white text-sm underline mb-4"
          >
            ← 返回常見問題
          </button>
          {localState.conversationHistory.length > 0 && (
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-white font-medium mb-2">最近的問題：</p>
              <p className="text-white/90 text-sm">
                {localState.conversationHistory[localState.conversationHistory.length - 1].question}
              </p>
              <p className="text-white/70 text-xs mt-2">
                {localState.conversationHistory[localState.conversationHistory.length - 1].answer}
              </p>
            </div>
          )}
          
          {/* Display follow-up suggestions if available */}
          {localState.followUpQuestions.length > 0 && (
            <FollowUpSuggestions
              suggestions={localState.followUpQuestions}
              onSuggestionClick={handleFollowUpClick}
              maxSuggestions={2}
            />
          )}
          <div className="text-center text-white/80 italic">
            請在右側聊天框中繼續對話
          </div>
        </div>
      )}
    </div>
  );
}

// Question Button Component with Chinese text support and consistent styling
export function QuestionButton({ 
  question, 
  onClick, 
  variant = 'primary', 
  className = '' 
}: QuestionButtonProps) {
  const baseClasses = "px-6 py-3 rounded-xl font-medium transition-all duration-300 text-white shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95 text-left w-full";
  const variantClasses = variant === 'primary' 
    ? "bg-white/20 hover:bg-white/30 border-2 border-white/30 hover:border-white/50" 
    : "bg-white/10 hover:bg-white/20 border border-white/20 hover:border-white/30";

  return (
    <button
      className={`${baseClasses} ${variantClasses} ${className}`}
      onClick={() => onClick(question)}
      style={{
        // Ensure proper Chinese text rendering with optimized font stack
        fontFamily: '"Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", system-ui, -apple-system, "Segoe UI", sans-serif',
        lineHeight: '1.7',
        letterSpacing: '0.02em',
        textAlign: 'left' as const,
        wordBreak: 'break-word' as const,
        // Ensure Chinese characters display properly
        unicodeBidi: 'normal',
        direction: 'ltr' as const
      }}
      // Ensure proper Chinese text handling
      lang="zh-CN"
    >
      <span className="block">
        {question}
      </span>
    </button>
  );
}

// Follow-up Suggestions Component with enhanced click handler integration
export function FollowUpSuggestions({ 
  suggestions, 
  onSuggestionClick, 
  maxSuggestions 
}: FollowUpSuggestionsProps) {
  // Ensure suggestions is an array and limit to maxSuggestions
  const validSuggestions = Array.isArray(suggestions) ? suggestions : [];
  const displaySuggestions = validSuggestions.slice(0, maxSuggestions);

  // Don't render if no suggestions
  if (displaySuggestions.length === 0) {
    return null;
  }

  // Enhanced click handler that preserves Chinese text and triggers proper submission
  const handleSuggestionClick = async (suggestion: string) => {
    try {
      // Ensure Chinese text preservation
      const preservedSuggestion = suggestion.trim();
      
      // Call the parent's click handler which now uses appendMessage
      await onSuggestionClick(preservedSuggestion);
    } catch (error) {
      console.error('Error handling follow-up suggestion click:', error);
    }
  };

  return (
    <div 
      className="flex flex-col gap-3 mt-6 p-4 bg-white/10 rounded-xl border border-white/20"
      style={{
        // Ensure proper Chinese text rendering
        fontFamily: '"Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", system-ui, sans-serif'
      }}
      lang="zh-CN"
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 bg-white/60 rounded-full"></div>
        <p className="text-white text-sm font-medium">
          相關問題建議：
        </p>
      </div>
      
      <div className="space-y-2">
        {displaySuggestions.map((suggestion, index) => (
          <button
            key={`follow-up-${index}`}
            className="w-full px-4 py-3 text-left bg-white/5 hover:bg-white/15 border border-white/20 hover:border-white/40 rounded-lg transition-all duration-200 text-white/90 hover:text-white text-sm group"
            onClick={() => handleSuggestionClick(suggestion)}
            style={{
              // Optimized Chinese text rendering
              fontFamily: '"Noto Sans CJK SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", system-ui, sans-serif',
              lineHeight: '1.6',
              letterSpacing: '0.01em',
              wordBreak: 'break-word' as const,
              unicodeBidi: 'normal',
              direction: 'ltr' as const
            }}
            lang="zh-CN"
          >
            <div className="flex items-center justify-between">
              <span className="flex-1">
                {suggestion}
              </span>
              <span className="ml-2 text-white/40 group-hover:text-white/60 transition-colors duration-200">
                →
              </span>
            </div>
          </button>
        ))}
      </div>
      
      <div className="mt-2 text-center">
        <p className="text-white/50 text-xs">
          點擊問題將自動填入聊天框
        </p>
      </div>
    </div>
  );
}