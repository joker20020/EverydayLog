# Introduction
Daily computer operation logs based on agent and VLM

# Usage
## clone this repo
```bash
git clone 
```
## install dependencies
```bash
uv sync
```
## run
```bash
uv run main.py
```

# Configure
```python
# The number of images to send to VLM = summary_freq // shot_freq
shot_freq = 10 # screenshot frequency
summary_freq = 60 # summary frequency(call VLM)
force_width, force_height = (1280, 720) # force resolution
```
