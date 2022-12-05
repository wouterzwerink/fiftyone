const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");
import * as http from "http";
import { ChildProcess, spawn } from "child_process";
import * as fs from "fs";

interface ProcessRunnerBaseConfig {}
abstract class ProcessRunner {
  protected process: ChildProcess;

  abstract start(config: ProcessRunnerBaseConfig): void;

  public stop() {
    this.process.kill();
  }
}
class PythonRunner extends ProcessRunner {
  start({ file }: ProcessRunnerBaseConfig & { file: string }) {
    console.log("starting", file);
    this.process = spawn("python", [`/tmp/${file}`]);
    this.process.stdout.on("data", (data) => {
      console.log(data.toString());
    });
  }
}

class CypressRunner extends ProcessRunner {
  start() {
    this.process = spawn("cypress", ["open"]);
    this.process.stdout.on("data", (data) => {
      console.log(data.toString());
    });
  }
}

class ProcessManager {
  private server: http.Server;
  private processes: Map<string, PythonRunner> = new Map();
  start() {
    const cypressRunner = new CypressRunner();
    cypressRunner.start();

    const app = express();
    app.use(bodyParser.json());
    app.use(cors());
    app.post("/exec", (req, res) => {
      const id = Math.random().toString().substring(2);
      const runner = new PythonRunner();
      const pythonFile = `${id}.py`;
      fs.writeFileSync(`/tmp/${pythonFile}`, req.body.py, "utf-8");
      runner.start({ file: pythonFile });
      this.processes.set(id, runner);
      res.send({ id });
    });
    app.post("/stop/:id", (req, res) => {
      const proc = this.processes.get(req.params.id);

      if (proc) {
        proc.stop();
        res.sendStatus(200);
      } else {
        res.sendStatus(404);
      }
    });

    this.server = http.createServer(app);
    this.server.listen(3005);
  }
  stopAll() {
    for (let [id, runner] of Object.entries(this.processes)) {
      runner.stop();
    }
  }

  stop() {
    this.server.close();
  }
}

export async function start() {
  const pm = new ProcessManager();
  pm.start();
}
