"""Vercel entrypoint: exposes the Dash app's Flask server as `app`.
This folder is a slim copy of the website for Vercel (no scipy/pyarrow, so it fits the size limit)."""
from flask import Flask

from dash_app import server

app: Flask = server
