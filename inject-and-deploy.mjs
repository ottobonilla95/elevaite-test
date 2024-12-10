import fs from "fs";
import path from "path";
import { exec, spawn } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

const appsDir = path.resolve("./apps");
const storageFilePath = path.resolve("./exampleFolder/variables.json");

let storageData;
try {
  const storageFile = fs.readFileSync(storageFilePath, "utf-8");
  storageData = JSON.parse(storageFile);
} catch (err) {
  console.error(`Failed to load or parse ${storageFilePath}:`, err.message);
  process.exit(1);
}

const apps = fs.readdirSync(appsDir).filter((entry) => {
  const appPath = path.join(appsDir, entry);
  return fs.statSync(appPath).isDirectory(); // We ensure to only process directories
});

async function setupAndStartApp(appName) {
  const appData = storageData[appName];
  if (!appData) {
    console.log(`No configuration found for app: ${appName}`);
    return;
  }

  const { common, ...appSpecificData } = appData;

  // We inject common and app-specific environment variables
  if (common) {
    for (const [key, value] of Object.entries(common)) {
      process.env[key] = value;
    }
  }
  for (const [key, value] of Object.entries(appSpecificData)) {
    process.env[key] = value;
  }

  console.log(`Environment variables injected for app: ${appName}`);

  // We deploy the app
  const appPath = path.join(appsDir, appName);

  console.log(`Building app: ${appName}...`);
  try {
    await execAsync("npm run build", { cwd: appPath, env: process.env });
    console.log(`App ${appName} built successfully.`);
  } catch (err) {
    console.error(`Failed to build app ${appName}:\n${err.message}`);
    return; // Skip starting the app if build fails
  }

  console.log(`Starting app: ${appName}...`);
  try {
    const child = spawn("npm", ["start"], {
      cwd: appPath,
      env: process.env,
      stdio: "inherit", // Forward output to the parent process
      shell: true, // Allow commands to run in the shell
    });

    child.on("error", (err) => {
      console.error(`Failed to start app ${appName}:\n${err.message}`);
    });

    child.on("exit", (code) => {
      if (code !== 0) {
        console.error(`App ${appName} exited with code ${code}.`);
      } else {
        console.log(`App ${appName} started successfully.`);
      }
    });
  } catch (err) {
    console.error(`Failed to start app ${appName}:\n${err.message}`);
  }
}

// Process each app
(async () => {
  for (const appName of apps) {
    try {
      await setupAndStartApp(appName);
    } catch (e) {
      console.error(`Error preventing "${appName}" from starting: ${e}`);
      continue;
    }
  }
})();
