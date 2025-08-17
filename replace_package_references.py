import os
from pathlib import Path

PACKAGE_TO_PROJECT = {
    "Microsoft.CodeAnalysis.Analyzers": "src/Analyzers/Core/Analyzers/Analyzers.shproj",
    "Microsoft.CodeAnalysis.Common": "src/Compilers/Core/Portable/Microsoft.CodeAnalysis.csproj",
    "Microsoft.CodeAnalysis.CSharp": "src/Compilers/CSharp/Portable/Microsoft.CodeAnalysis.CSharp.csproj",
    "Microsoft.CodeAnalysis.CSharp.Workspaces": "src/Workspaces/CSharp/Portable/Microsoft.CodeAnalysis.CSharp.Workspaces.csproj",
    "Microsoft.CodeAnalysis.Workspaces.Common": "src/Workspaces/Core/Portable/Microsoft.CodeAnalysis.Workspaces.csproj",
}

def process_file(file_path: Path, repo_root: Path):
    with file_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if "<PackageReference" in line_stripped and "Include=" in line_stripped:
            for pkg, target_proj in PACKAGE_TO_PROJECT.items():
                if f'Include="{pkg}"' in line_stripped:
                    # Scan upward and downward for <Otherwise>
                    otherwise_found = False
                    # Upward scan
                    for j in range(i-1, -1, -1):
                        if "<Otherwise>" in lines[j]:
                            otherwise_found = True
                            break
                        if "<ItemGroup" in lines[j] or "<Choose" in lines[j]:
                            break
                    # Downward scan
                    if not otherwise_found:
                        for j in range(i+1, len(lines)):
                            if "</Otherwise>" in lines[j]:
                                otherwise_found = True
                                break
                            if "</ItemGroup>" in lines[j] or "</Choose>" in lines[j]:
                                break

                    if otherwise_found:
                        print(f"Skipped (Otherwise present) in {file_path} at line {i + 1}")
                        break  # Skip this PackageReference

                    # Replace with ProjectReference silently
                    rel_path = os.path.relpath(repo_root / target_proj, start=file_path.parent)
                    rel_path = rel_path.replace("\\", "/")
                    lines[i] = f'    <ProjectReference Include="{rel_path}" />\n'
                    modified = True
                    break

    if modified:
        with file_path.open("w", encoding="utf-8") as f:
            f.writelines(lines)

def process_all_projects(repo_root: Path):
    for ext in ("*.csproj", "*.vbproj"):
        for proj_file in repo_root.rglob(ext):
            process_file(proj_file, repo_root)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python replace_package_refs_text.py <path-to-repo-root>")
        sys.exit(1)

    repo_root = Path(sys.argv[1]).resolve()
    if not repo_root.exists():
        print(f"Folder {repo_root} does not exist")
        sys.exit(1)

    process_all_projects(repo_root)

