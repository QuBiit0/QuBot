"use client";

import { useState, useEffect } from "react";
import {
  Key,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  Search,
  Shield,
  RefreshCw,
  Check,
  X,
  Tag,
} from "lucide-react";

interface Secret {
  name: string;
  category: string;
  description: string | null;
  tags: string[] | null;
  created_at: string;
  masked_value: string;
}

const CATEGORIES = [
  { id: "api_key", label: "API Key", icon: "🔑" },
  { id: "credentials", label: "Credentials", icon: "🔐" },
  { id: "token", label: "Token", icon: "🎫" },
  { id: "certificate", label: "Certificate", icon: "📜" },
  { id: "password", label: "Password", icon: "🔏" },
  { id: "secret_key", label: "Secret Key", icon: "🔏" },
  { id: "other", label: "Other", icon: "📦" },
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SecretsPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showValue, setShowValue] = useState<Record<string, boolean>>({});
  const [secretValues, setSecretValues] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState<string | null>(null);

  const [newSecret, setNewSecret] = useState({
    name: "",
    value: "",
    category: "api_key",
    description: "",
    tags: "",
  });

  useEffect(() => {
    loadSecrets();
  }, []);

  const loadSecrets = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/secrets`);
      if (res.ok) {
        const data = await res.json();
        setSecrets(data.secrets || []);
      }
    } catch {
      console.error("Failed to load secrets");
    }
    setLoading(false);
  };

  const createSecret = async () => {
    if (!newSecret.name || !newSecret.value) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/secrets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newSecret.name,
          value: newSecret.value,
          category: newSecret.category,
          description: newSecret.description || null,
          tags: newSecret.tags ? newSecret.tags.split(",").map((t) => t.trim()) : null,
        }),
      });

      if (res.ok) {
        setShowCreateModal(false);
        setNewSecret({ name: "", value: "", category: "api_key", description: "", tags: "" });
        loadSecrets();
      }
    } catch {
      console.error("Failed to create secret");
    }
    setLoading(false);
  };

  const deleteSecret = async (name: string) => {
    if (!confirm(`Delete secret "${name}"?`)) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/secrets/${name}`, {
        method: "DELETE",
      });

      if (res.ok) {
        loadSecrets();
      }
    } catch {
      console.error("Failed to delete secret");
    }
    setLoading(false);
  };

  const revealSecret = async (name: string) => {
    if (showValue[name]) {
      setShowValue((prev) => ({ ...prev, [name]: false }));
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/secrets/${name}`);
      if (res.ok) {
        const data = await res.json();
        setSecretValues((prev) => ({ ...prev, [name]: data.value }));
        setShowValue((prev) => ({ ...prev, [name]: true }));
      }
    } catch {
      console.error("Failed to reveal secret");
    }
  };

  const copySecret = async (name: string) => {
    const value = secretValues[name];
    if (!value) return;

    await navigator.clipboard.writeText(value);
    setCopied(name);
    setTimeout(() => setCopied(null), 2000);
  };

  const filteredSecrets = secrets.filter((s) => {
    const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !selectedCategory || s.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const secretsByCategory = CATEGORIES.map((cat) => ({
    ...cat,
    secrets: filteredSecrets.filter((s) => s.category === cat.id),
  })).filter((cat) => cat.secrets.length > 0 || !selectedCategory);

  return (
    <div className="flex h-screen" style={{ backgroundColor: darkMode ? "#0d1117" : "#f6f8fa" }}>
      <div className="flex-1 flex flex-col">
        <header
          className="border-b px-6 py-4 flex items-center justify-between"
          style={{
            backgroundColor: darkMode ? "#161b22" : "#ffffff",
            borderColor: darkMode ? "#30363d" : "#d0d7de",
          }}
        >
          <div className="flex items-center gap-4">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)" }}
            >
              <Shield className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
              Secrets Manager
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              style={{
                backgroundColor: darkMode ? "rgba(255,255,255,0.05)" : "#eaeef2",
                color: darkMode ? "#e6edf3" : "#1e293b",
              }}
            >
              {darkMode ? "Light" : "Dark"}
            </button>
          </div>
        </header>

        <div className="flex-1 p-6 overflow-auto">
          <div className="max-w-5xl mx-auto space-y-6">
            <div
              className="p-6 rounded-xl"
              style={{
                backgroundColor: darkMode ? "#161b22" : "#ffffff",
                border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
              }}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                    Secure Storage
                  </h2>
                  <p className="text-sm" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    Store API keys, tokens, and credentials securely
                  </p>
                </div>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors"
                  style={{ backgroundColor: "#f59e0b", color: "#ffffff" }}
                >
                  <Plus className="w-4 h-4" />
                  Add Secret
                </button>
              </div>

              <div className="flex gap-4 mb-6">
                <div
                  className="flex-1 flex items-center gap-2 px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                >
                  <Search className="w-4 h-4" style={{ color: darkMode ? "#8b949e" : "#57606a" }} />
                  <input
                    type="text"
                    placeholder="Search secrets..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="flex-1 bg-transparent outline-none text-sm"
                    style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}
                  />
                </div>

                <select
                  value={selectedCategory || ""}
                  onChange={(e) => setSelectedCategory(e.target.value || null)}
                  className="px-4 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                >
                  <option value="">All Categories</option>
                  {CATEGORIES.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-6 h-6 animate-spin" style={{ color: "#f59e0b" }} />
                </div>
              ) : filteredSecrets.length === 0 ? (
                <div className="text-center py-12">
                  <Key className="w-12 h-12 mx-auto mb-4" style={{ color: darkMode ? "#8b949e" : "#57606a" }} />
                  <p style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                    {search || selectedCategory ? "No secrets match your filters" : "No secrets stored yet"}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {secretsByCategory.map((category) => (
                    <div key={category.id}>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-lg">{category.icon}</span>
                        <h3 className="font-medium" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                          {category.label}
                        </h3>
                        <span
                          className="text-xs px-2 py-0.5 rounded"
                          style={{ backgroundColor: darkMode ? "#21262d" : "#eaeef2", color: darkMode ? "#8b949e" : "#57606a" }}
                        >
                          {category.secrets.length}
                        </span>
                      </div>

                      <div className="space-y-2">
                        {category.secrets.map((secret) => (
                          <div
                            key={secret.name}
                            className="p-4 rounded-lg flex items-center justify-between"
                            style={{
                              backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                              border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                            }}
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-medium" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                                  {secret.name}
                                </span>
                                {copied === secret.name && (
                                  <span className="text-xs flex items-center gap-1" style={{ color: "#22c55e" }}>
                                    <Check className="w-3 h-3" /> Copied
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <code
                                  className="text-xs font-mono"
                                  style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                                >
                                  {showValue[secret.name]
                                    ? secretValues[secret.name] || "***"
                                    : secret.masked_value}
                                </code>
                              </div>
                              {secret.description && (
                                <p className="text-xs mt-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                                  {secret.description}
                                </p>
                              )}
                              {secret.tags && secret.tags.length > 0 && (
                                <div className="flex gap-1 mt-2">
                                  {secret.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="text-xs px-1.5 py-0.5 rounded flex items-center gap-1"
                                      style={{ backgroundColor: "rgba(245,158,11,0.1)", color: "#f59e0b" }}
                                    >
                                      <Tag className="w-3 h-3" />
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => revealSecret(secret.name)}
                                className="p-2 rounded-lg transition-colors hover:bg-white/5"
                                style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                              >
                                {showValue[secret.name] ? (
                                  <EyeOff className="w-4 h-4" />
                                ) : (
                                  <Eye className="w-4 h-4" />
                                )}
                              </button>
                              {showValue[secret.name] && (
                                <button
                                  onClick={() => copySecret(secret.name)}
                                  className="p-2 rounded-lg transition-colors hover:bg-white/5"
                                  style={{ color: darkMode ? "#8b949e" : "#57606a" }}
                                >
                                  <Copy className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => deleteSecret(secret.name)}
                                className="p-2 rounded-lg transition-colors hover:bg-white/5"
                                style={{ color: "#f85149" }}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div
            className="w-full max-w-lg rounded-xl p-6"
            style={{
              backgroundColor: darkMode ? "#161b22" : "#ffffff",
              border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold" style={{ color: darkMode ? "#e6edf3" : "#1e293b" }}>
                Add New Secret
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded hover:bg-white/5"
                style={{ color: darkMode ? "#8b949e" : "#57606a" }}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Name *
                </label>
                <input
                  type="text"
                  value={newSecret.name}
                  onChange={(e) => setNewSecret({ ...newSecret, name: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, "") })}
                  placeholder="e.g., openai_api_key"
                  className="w-full px-3 py-2 rounded-lg text-sm font-mono"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Value *
                </label>
                <textarea
                  value={newSecret.value}
                  onChange={(e) => setNewSecret({ ...newSecret, value: e.target.value })}
                  placeholder="Secret value..."
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg text-sm font-mono resize-none"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Category
                </label>
                <select
                  value={newSecret.category}
                  onChange={(e) => setNewSecret({ ...newSecret, category: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Description
                </label>
                <input
                  type="text"
                  value={newSecret.description}
                  onChange={(e) => setNewSecret({ ...newSecret, description: e.target.value })}
                  placeholder="What is this secret for?"
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: darkMode ? "#8b949e" : "#57606a" }}>
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={newSecret.tags}
                  onChange={(e) => setNewSecret({ ...newSecret, tags: e.target.value })}
                  placeholder="production, aws, api"
                  className="w-full px-3 py-2 rounded-lg text-sm"
                  style={{
                    backgroundColor: darkMode ? "#0d1117" : "#f6f8fa",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                    border: `1px solid ${darkMode ? "#30363d" : "#d0d7de"}`,
                  }}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg text-sm font-medium"
                  style={{
                    backgroundColor: darkMode ? "#21262d" : "#eaeef2",
                    color: darkMode ? "#e6edf3" : "#1e293b",
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={createSecret}
                  disabled={!newSecret.name || !newSecret.value || loading}
                  className="flex-1 px-4 py-2 rounded-lg text-sm font-medium"
                  style={{
                    backgroundColor: newSecret.name && newSecret.value ? "#f59e0b" : "rgba(245,158,11,0.3)",
                    color: "#ffffff",
                  }}
                >
                  {loading ? "Saving..." : "Save Secret"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
