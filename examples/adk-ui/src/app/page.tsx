"use client";

import { StructuredOutputPreview } from "@/components/structured-output-preview";
import { WeatherCard } from "@/components/weather";
import { AgentState } from "@/lib/types";
import {
  useCoAgent,
  useFrontendTool,
  useRenderToolCall,
} from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotChat } from "@copilotkit/react-ui";
import { useState } from "react";

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");

  // 🪁 Frontend Actions: https://docs.copilotkit.ai/adk/frontend-actions
  useFrontendTool({
    name: "setThemeColor",
    parameters: [
      {
        name: "themeColor",
        description: "The theme color to set. Make sure to pick nice colors.",
        required: true,
      },
    ],
    handler({ themeColor }) {
      setThemeColor(themeColor);
    },
  });

  return (
    <main
      style={
        { "--copilot-kit-primary-color": themeColor } as CopilotKitCSSProperties
      }
      className="h-screen flex"
    >
      {/* 左側聊天室 */}
      <div className="w-1/2 h-full border-r border-gray-200 flex flex-col">
        <CopilotChat
          labels={{
            title: "AI Assistant",
            initial: "👋 Hi! I can help you generate structured data and more.",
          }}
          suggestions={[
            {
              title: "Generate Data",
              message: "Generate a sample user profile with structured data.",
            },
            {
              title: "Weather Info",
              message: "Get the weather in Tokyo.",
            },
            {
              title: "Theme Change",
              message: "Set the theme to blue.",
            },
            {
              title: "JSON Output",
              message: "Create a JSON structure for a product catalog.",
            },
          ]}
        />
      </div>
      
      {/* 右側預覽區域 */}
      <div className="w-1/2 h-full">
        <YourMainContent themeColor={themeColor} />
      </div>
    </main>
  );
}

function YourMainContent({ themeColor }: { themeColor: string }) {
  // 🪁 Shared State: https://docs.copilotkit.ai/adk/shared-state
  const { state, setState } = useCoAgent<AgentState>({
    name: "my_agent",
    initialState: {
      structuredData: null,
      lastOutput: null,
    },
  });

  //🪁 Generative UI: https://docs.copilotkit.ai/adk/generative-ui
  useRenderToolCall(
    {
      name: "get_weather",
      description: "Get the weather for a given location.",
      parameters: [{ name: "location", type: "string", required: true }],
      render: ({ args, result }) => {
        return <WeatherCard location={args.location} themeColor={themeColor} />;
      },
    },
    [themeColor],
  );

  return (
    <div
      style={{ backgroundColor: themeColor }}
      className="h-full w-full flex justify-center items-center transition-colors duration-300 p-6"
    >
      <StructuredOutputPreview state={state} setState={setState} themeColor={themeColor} />
    </div>
  );
}
