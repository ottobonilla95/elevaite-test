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
  return fs.statSync(appPath).isDirectory();
});

const apps = targetAppName
  ? allApps.includes(targetAppName)
    ? [targetAppName]
    : (() => {
        console.error(
          `App "${targetAppName}" does not exist in the "apps" directory.`
        );
        process.exit(1);
      })()
  : allApps;

async function setupAndStartApp(appName) {
  const appData = storageData[appName];
  if (!appData) {
    console.log(`No configuration found for app: ${appName}`);
    return;
  }

  // We merge common and app-specific variables
  const { __common, ...appSpecificData } = appData;
  const envObject = { ...(__common || {}), ...appSpecificData };

  // We create a temporary .env file for Docker Compose
  const envContent = Object.entries({ ...storageData.__common, ...envObject })
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");

  const tempEnvPath = path.resolve(`./.env.${appName}`);
  fs.writeFileSync(tempEnvPath, envContent);

  console.log(`Starting docker-compose for app: ${appName}...`);

  const composeFilePath = path.resolve("./docker-compose.frontend.yaml");
  const composeCommand = `docker-compose --env-file ${tempEnvPath} -f ${composeFilePath} up -d ${appName}`;

  try {
    await execAsync(composeCommand);
    console.log(`App ${appName} started successfully using docker-compose.`);
  } catch (err) {
    console.error(
      `Failed to start app ${appName} with docker-compose:\n${err.message}`
    );
  } finally {
    // We clean up the temporary env file
    fs.unlinkSync(tempEnvPath);
  }
}

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
