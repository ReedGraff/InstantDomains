For my backend I am using FastAPI, python, pydantic, and firebase. I'm using Vite and TSX for the frontend for reference.

Your goal is to write simple no bs code that solves exactly what I asked for in as little code as possible. Make sure to not change anything else other than what I mentioned. The simpler the better. Keep all code in the indentation provided (most likely 4 space tabs for backend). Do not add or delete new line spaces or spaces. Never delete comments.

If anything ever requires authentication, it must be handled by the firebase user JWT key (from firebase on login), or the API key found in the firestore billing collection for that user. You should always pass and process this as a bearer token in the authentication header.

This application is an api backend, hosting:
1. All background tasks (like a normal api): For example, a function that uses ai to generate content based on a prompt, and runs in the background without blocking the main thread.
    * All AI calls should be called as a background task, and should not interrupt main thread tasks, nor return a response object like json, only a response code such as 200 for success with details `raise HTTPException(status_code=400, detail="Invalid base64 string provided in fileData.")` or `return Response(status_code=202)` are acceptable. Do not use asyncio.create_task for this, just use the fastapi background tasks.
```python
router = APIRouter()

async def generate_content(prompt: str):
    # This function will be executed in the background
    # It can contain AI model calls or other time-consuming operations
    await asyncio.sleep(5)  # Simulate a long-running task
    print(f"Generating content for: {prompt}")
    # ... AI processing logic ...

@router.post("/")
async def start_generation(
    prompt: str, 
    background_tasks: BackgroundTasks
):
    task = create_background_task(generate_content, prompt)
    return await task(background_tasks)
```
    * Here is a common pattern to follow for background tasks:
```python
async def generate_location_data(data: LocationRequest, user: User):
    """
    Generate location data for target businesses within specified area.
    This function is executed in the background.
    
    Args:
        data (LocationRequest): The request data containing location and business details.
        user (User): The authenticated user requesting the location data.
    """
    try:
        # Simulate a long-running task
        await asyncio.sleep(5)
        # Here you would implement the logic to generate location data
        logger.info(f"Generated location data for user {user.id} with data: {data}")
    except Exception as e:
        logger.error(f"Error generating location data: {e}", exc_info=True)

@router.post("")
async def location_finder(
    data: LocationRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """
    Initiate an asynchronous job to generate location data for target businesses within specified area.
    Returns only a status code.
    """
    try:
        background_tasks.add_task(generate_location_data, data, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    return Response(status_code=202)
```
    * Sometimes an endpoint will in turn call 2 or 3 other endpoints. when this happens, make sure to use the same background task pattern as above, and don't use asyncio.create_task or any other async task creation method. Always use the FastAPI background tasks.

This is my project structure:
- src/api/
    - lib/
        - db.py # handles firebase db and firebase auth and firebase storage
        - globTypes.py # contains all the global types for the backend, such as pydantic models and firebase types
        - logger_config.py # handles the logger for the whole application
        - other utility files
    - pages/ # this is effectively a page router, similar to next.js
        - index.py # root page
        - visits/ # represents the visits page, which is a subpage of the root page
            - index.py # '/visits' page
            - [id].py # '/visits/id' details page, where id is the visit id
        - visits2.py # an example of a '/visits2' page
        ... # other pages

Here are some additional guidelines to follow when writing code for this project:
- Environment variables: I have an `.env` file in the root of the project, and you should use `from dotenv import load_dotenv` and `os.getenv()` to access environment variables. Do not hardcode any sensitive information.
- naming conventions: use snake_case for all variables and functions, and camelCase for all classes.
- docstrings: use docstrings for all functions and classes, and make sure to include the parameters and return types. Use the google style for docstrings (Args, Returns, Raises, and Examples)
- preambles: avoid 'here is the code'. similarly avoid 'Modification Start' or 'Modification End:'
- prop-drilling: make sure to following best practice, and use context, hooks, or providers for handling shared data across my codebase. Referencing all data points following a singleton pattern, as to not produce more code than necessary.
- schema, make sure to adhere to my schema, provided in the globTypes.py file.
- form handling: make sure to have single variables representing all of the form data as one value (/object like a dictionary), not as individual setters and getters... one for all inputs in a form
- libraries: do not import any new libraries, unless asked for. You may however mention it, in a suffix to the solution.
- Dates: All dates will be stored on the backend as a firebase time stamp object. (AKA firestore.SERVER_TIMESTAMP), for every date, you must parse it into an object, and then convert it into the local time the browser is running on.
- be frugal when adding comments, and don't spam them on every change, but keep any comments that already exist.
- Logs: Use the python logger for everything (from lib.logger_config import logger # I wanted to use a single logger for my whole application for simplicity), not print statement. Additionally, make absolutely certain to be verbose when it comes specifically to logging errors... as in always log the stacktrace so I can determine where the bug is coming from and solve it...  
- File Handling: Make sure to use asyncio/aiofiles for everything file related to make sure to not block the main threads, however, also use local routing using the following code: 
```python
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
os.path.join(__location__, '../keys/describe-final-firebase-adminsdk-fbsvc-796846473b.json')
```
- When it comes to updating anything in firebase, make sure to always use 'set' with 'merge=True' to update fields in the document or create it if it doesn't exists. Never just use update or create or set without the merge parameter.
