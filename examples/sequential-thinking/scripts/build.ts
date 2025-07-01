import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";
import path from "path";

const execAsync = promisify(exec);

async function copyDir(src: string, dest: string) {
  // Create destination directory
  fs.mkdirSync(dest, { recursive: true });

  // Read directory contents
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

async function build() {
  console.log("🏗️  Building the application...");

  // Create dist directory if it doesn't exist
  const distDir = path.join(process.cwd(), "dist");
  if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
  }

  try {
    // Run TypeScript compiler
    console.log("Running TypeScript compiler...");
    await execAsync("tsc --project tsconfig.json");
    
    console.log("✅ TypeScript compilation completed successfully");
    
    // Copy any non-TypeScript files
    console.log("Copying additional files...");
    const srcDir = path.join(process.cwd(), "src");
    const distSrcDir = path.join(distDir, "src");
    await copyDir(srcDir, distSrcDir);
    
    console.log("✅ Build completed successfully!");
  } catch (error) {
    console.error("❌ Build failed:", error);
    process.exit(1);
  }
}

// Run the build process
build().catch(console.error); 