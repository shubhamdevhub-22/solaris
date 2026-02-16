source venv/bin/activate

python manage.py collectstatic
python manage.py seed

sudo systemctl daemon-reload

sudo systemctl restart nginx
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

sudo systemctl daemon-reload
sudo systemctl start celery
sudo systemctl enable celery
