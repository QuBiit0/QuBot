# Qubot Frontend

A modern, real-time multi-agent AI platform frontend built with Next.js, React, and TypeScript.

## 🚀 Features

- **Coworking Office**: Visual office metaphor with agent avatars working in real-time
- **Mission Control**: Kanban board for task management with drag & drop
- **Agent Management**: Create, configure, and manage AI agents
- **Real-time Updates**: WebSocket integration for live agent and task updates
- **Chat Interface**: Direct communication with the orchestrator
- **Tools & Integrations**: Extensible tool system

## 🛠️ Tech Stack

- **Framework**: Next.js 15 + React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Real-time**: WebSocket
- **Canvas**: React Konva
- **Animations**: Framer Motion
- **Drag & Drop**: @dnd-kit
- **Icons**: Lucide React

## 📁 Project Structure

```
app/
├── dashboard/           # Coworking office with agent visualization
├── mission-control/     # Kanban board
├── agents/             # Agent management
├── chat/               # Orchestrator chat
├── tools/              # Tools & integrations
└── settings/           # Configuration

components/
├── kanban/             # Kanban board components
├── coworking/          # Office canvas & agent avatars
├── layout/             # Sidebar, Activity panel
├── wizard/             # Agent creation wizard
└── ui/                 # Shared UI components

hooks/                  # Custom React hooks
store/                  # Zustand stores
lib/                    # Utilities & API client
types/                  # TypeScript definitions
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

## 🔌 Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 📝 Key Features

### Coworking Office
- Visual representation of agents on a canvas
- Three layout strategies based on team size
- Real-time status updates (working, thinking, talking, idle)
- Click agents to see details
- Animated avatars with state-specific behaviors

### Mission Control (Kanban)
- Drag & drop task management
- 5 columns: Backlog → To Do → In Progress → Review → Done
- Priority levels with color coding
- Optimistic updates for smooth UX

### Agent Creation Wizard
- 4-step wizard for creating new agents
- Domain and role selection
- AI model configuration (GPT-4, GPT-4 Turbo, GPT-3.5)
- Temperature/creativity adjustment

### Real-time Updates
- WebSocket connection with auto-reconnection
- Exponential backoff for reconnection
- Activity feed with filtered notifications

## 🧪 Mock Data

The application includes mock data for testing. Data is automatically loaded when the app starts in development mode.

## 📦 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## 🔒 Security

- JWT token-based authentication
- Environment variables for sensitive config
- Error boundaries for graceful error handling

## 📄 License

MIT License - See LICENSE file for details
