FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install ipython==8.17.2 jupyter==1.0.0 langchain==0.0.331 langchain-experimental==0.0.38 langsmith==0.0.60 openai==0.28.1 pandas==2.1.2 panel==1.3.1 plotly==5.18.0 python-dotenv==1.0.0 bokeh tabulate


# Copy your application code
COPY . /app

# Expose the application port (e.g., 8080)
EXPOSE 8080

# Start the Panel app
CMD ["panel", "serve", "app.py", "--port=8080", "--address=0.0.0.0", "--allow-websocket-origin=*"]