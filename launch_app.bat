@echo off
echo 🤖 AI Customer Support System - Complete Launch
echo ================================================
echo.

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Generating sample dataset...
python -c "from dataset_generator import DatasetGenerator; dg = DatasetGenerator(); dg.generate_csv_dataset('sample_tickets.csv'); print('Sample dataset created!')"

echo.
echo Starting Customer Support System...
echo The app will open at: http://localhost:8501
echo.

streamlit run main.py --server.port 8501

pause