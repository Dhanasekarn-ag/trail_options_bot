# Create a simple test script
@"
from dotenv import load_dotenv
import os
load_dotenv()
print('PAPER_TRADING value:', repr(os.getenv('PAPER_TRADING')))
print('UPSTOX_API_KEY value:', repr(os.getenv('UPSTOX_API_KEY')))
"@ | Out-File -FilePath test_env.py -Encoding utf8
