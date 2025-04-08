import json
import docker
import tempfile
import os
from typing import Dict, Any
from threading import Timer

client = docker.from_env()

async def run_in_docker(code: str, language: str, input_data: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    try:
        # Create temporary file with the function code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file_path = os.path.abspath(f.name)
            f.write(f"""
{code}

if __name__ == "__main__":
    import json
    event = {json.dumps(input_data)}
    print(json.dumps(handler(event)))
            """)
        
        # Ensure temp file exists before execution
        f.close()

        # Run the container in detached mode for timeout control
        container = client.containers.run(
            "python-lambda",
            volumes={os.path.dirname(temp_file_path): {'bind': '/app', 'mode': 'rw'}},
            command=f"python /app/{os.path.basename(temp_file_path)}",
            detach=True,  # Required for timeout handling
            stdout=True,
            stderr=True
        )

        # Set up timeout enforcement
        def stop_container():
            try:
                container.stop(timeout=5)
            except docker.errors.APIError as e:
                print(f"Warning: Failed to stop container: {str(e)}")

        timer = Timer(timeout, stop_container)
        timer.start()

        try:
            # Wait for container to finish
            result = container.wait()
            output = container.logs(stdout=True, stderr=False).decode('utf-8')
            
            if result['StatusCode'] != 0:
                error_logs = container.logs(stderr=True).decode('utf-8')
                return {"error": f"Container exited with code {result['StatusCode']}: {error_logs}"}
            
            return json.loads(output)
        finally:
            # Cleanup resources
            timer.cancel()
            container.remove(force=True)
            os.unlink(temp_file_path)
        
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON output: {str(e)}"}
    except docker.errors.ContainerError as e:
        return {"error": f"Container failed: {e.stderr.decode('utf-8')}"}
    except docker.errors.APIError as e:
        return {"error": f"Docker API error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}