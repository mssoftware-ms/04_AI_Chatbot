#!/usr/bin/env node

/**
 * Claude-Flow Hive-Mind Starter
 * Initialisiert und startet das Multi-Agent System
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

// Konfiguration laden
const config = require('./claude-flow.config.js');
const agents = require('./agents.json');

class HiveMindStarter {
  constructor() {
    this.db = null;
    this.mcpServers = [];
    this.agents = agents.agents;
  }

  async init() {
    console.log('🐝 Initialisiere Claude-Flow Hive-Mind...\n');
    
    // 1. SQLite Datenbank initialisieren
    await this.initDatabase();
    
    // 2. MCP Server starten
    await this.startMCPServers();
    
    // 3. Agenten initialisieren
    await this.initAgents();
    
    // 4. Hive-Mind starten
    await this.startHiveMind();
  }

  async initDatabase() {
    console.log('📊 Initialisiere SQLite Memory System...');
    
    this.db = new sqlite3.Database(config.memory.database);
    
    // Tabellen erstellen
    const tables = [
      `CREATE TABLE IF NOT EXISTS swarm_state (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        state TEXT,
        queen_status TEXT,
        worker_count INTEGER
      )`,
      
      `CREATE TABLE IF NOT EXISTS agent_interactions (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        from_agent TEXT,
        to_agent TEXT,
        message TEXT,
        task_id TEXT
      )`,
      
      `CREATE TABLE IF NOT EXISTS task_history (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        task_id TEXT,
        description TEXT,
        assigned_to TEXT,
        status TEXT,
        result TEXT
      )`,
      
      `CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        agent_id TEXT,
        task_id TEXT,
        execution_time INTEGER,
        tokens_used INTEGER,
        success BOOLEAN
      )`
    ];
    
    for (const sql of tables) {
      await new Promise((resolve, reject) => {
        this.db.run(sql, (err) => {
          if (err) reject(err);
          else resolve();
        });
      });
    }
    
    console.log('✅ SQLite Memory System bereit\n');
  }

  async startMCPServers() {
    console.log('🔧 Starte MCP Server...');
    
    // Filesystem MCP Server
    if (config.mcp.filesystem.enabled) {
      console.log(`  - Filesystem Server auf Port ${config.mcp.filesystem.port}`);
      const fsServer = spawn('npx', [
        '@modelcontextprotocol/server-filesystem',
        config.mcp.filesystem.rootPath
      ], {
        env: { ...process.env, PORT: config.mcp.filesystem.port }
      });
      this.mcpServers.push(fsServer);
    }
    
    // Database MCP Server  
    if (config.mcp.database.enabled) {
      console.log(`  - Database Server auf Port ${config.mcp.database.port}`);
      // Hier würde der Database MCP Server gestartet
    }
    
    // Git MCP Server
    if (config.mcp.git.enabled) {
      console.log(`  - Git Server auf Port ${config.mcp.git.port}`);
      // Hier würde der Git MCP Server gestartet
    }
    
    console.log('✅ MCP Server gestartet\n');
  }

  async initAgents() {
    console.log('🤖 Initialisiere Agenten...');
    
    // Queen initialisieren
    console.log('  👑 Queen Agent:', this.agents.queen.name);
    
    // Worker initialisieren
    Object.entries(this.agents).forEach(([key, agent]) => {
      if (key !== 'queen') {
        console.log(`  🐝 ${agent.role}:`, agent.name);
      }
    });
    
    console.log('✅ Alle Agenten bereit\n');
  }

  async startHiveMind() {
    console.log('🚀 Starte Hive-Mind System...');
    console.log('='*60);
    
    // Claude-Flow Hive-Mind Befehl ausführen
    const hiveProcess = spawn('claude-flow', [
      'hive',
      'start',
      '--config', './claude-flow.config.js',
      '--agents', './agents.json',
      '--topology', config.hiveMode.topology,
      '--memory', config.memory.database
    ], {
      stdio: 'inherit'
    });
    
    hiveProcess.on('error', (err) => {
      console.error('❌ Fehler beim Starten des Hive-Mind:', err);
      this.cleanup();
    });
    
    // Graceful Shutdown
    process.on('SIGINT', () => {
      console.log('\n⚠️ Shutting down Hive-Mind...');
      this.cleanup();
    });
  }

  cleanup() {
    // MCP Server beenden
    this.mcpServers.forEach(server => server.kill());
    
    // Datenbank schließen
    if (this.db) {
      this.db.close();
    }
    
    console.log('👋 Hive-Mind beendet');
    process.exit(0);
  }
}

// Hauptprogramm
async function main() {
  console.clear();
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║           CLAUDE-FLOW HIVE-MIND SYSTEM v2.0.0           ║');
  console.log('╚══════════════════════════════════════════════════════════╝\n');
  
  const hiveMind = new HiveMindStarter();
  await hiveMind.init();
}

// Starten
main().catch(console.error);