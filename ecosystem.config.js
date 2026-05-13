module.exports = {
  apps: [{
    name: 'whatsapp-bot',
    script: 'venv/bin/uvicorn',
    args: 'main:app --host 0.0.0.0 --port 8000',
    interpreter: 'none',
    env: {
      PYTHONPATH: '.',
      # You can add more environment variables here if needed
    },
    restart_delay: 5000,
    max_restarts: 10,
    out_file: "./logs/out.log",
    error_file: "./logs/error.log",
    merge_logs: true,
    log_date_format: "YYYY-MM-DD HH:mm:ss"
  }]
};
