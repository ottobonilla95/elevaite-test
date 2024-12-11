// USAGE: npm run superfrontploy [-- APPNAME]
import fs from "fs";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

const appsDir = path.resolve("./apps");
const storageFilePath = path.resolve("./variables.json");

const targetAppName = process.argv[2];

let storageData;
try {
  const storageFile = fs.readFileSync(storageFilePath, "utf-8");
  storageData = JSON.parse(storageFile);
} catch (err) {
  console.error(`Failed to load or parse ${storageFilePath}:`, err.message);
  process.exit(1);
}

const allApps = fs.readdirSync(appsDir).filter((entry) => {
  const appPath = path.join(appsDir, entry);
  return fs.statSync(appPath).isDirectory(); // Ensure to only process directories
});

// Filter apps based on the input argument
const apps = targetAppName
  ? allApps.includes(targetAppName)
    ? [targetAppName] // If a valid app name is provided, we deploy only that app
    : (() => {
        console.error(
          `App "${targetAppName}" does not exist in the "apps" directory.`
        );
        process.exit(1);
      })()
  : allApps; // Deploy all apps if no argument is provided

async function setupAndStartApp(appName) {
  const appData = storageData[appName];
  if (!appData) {
    console.log(`No configuration found for app: ${appName}`);
    return;
  }

  const { __common, ...appSpecificData } = appData;

  // Prepare the environment variables
  const secrets = [];

  // Inject __common environment variables for all apps
  if (__common) {
    for (const [key, value] of Object.entries(__common)) {
      secrets.push(`${key}=${value}`);
    }
  }

  // Inject app-specific environment variables for this app
  for (const [key, value] of Object.entries(appSpecificData)) {
    secrets.push(`${key}=${value}`);
  }

  // Docker commands
  const appPath = path.join(appsDir, appName);
  const dockerBuildCommand = `docker build -t ${appName} -f ${path.resolve(appPath, "Dockerfile")} .`;

  // Create the env flag with secrets for the docker run command
  const envFlag = secrets.map((secret) => `--env ${secret}`).join(" ");
  const dockerStopRemoveCommand = `
    if docker ps -a --format '{{.Names}}' | grep -wq ${appName}; then
      docker stop ${appName} && docker rm ${appName};
    fi
  `;

  console.log(`Preparing to build and start app: ${appName} using Docker...`);

  try {
    // Dispose of any existing container with the same name
    await execAsync(dockerStopRemoveCommand);

    // Build the Docker image
    console.log(`Building app: ${appName} using Docker...`);
    await execAsync(dockerBuildCommand);
    console.log(`App ${appName} built successfully.`);
  } catch (err) {
    console.error(`Failed to build app ${appName}:\n${err.message}`);
    return; // Skip starting the app if build fails
  }

  console.log(`Starting app: ${appName} using Docker...`);
  try {
    const dockerRunCommand = `docker run --name ${appName} ${envFlag} ${appName}`;
    const child = exec(dockerRunCommand, { stdio: "inherit" });

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
    console.error(`Failed to deploy app ${appName}:\n${err.message}`);
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
  console.log("App(s) have been processed. Exiting..");
  process.exit(0);
})();
