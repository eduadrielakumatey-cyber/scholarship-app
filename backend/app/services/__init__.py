"""
app/services/__init__.py
Empty on purpose -- this package just groups business-logic modules
(scoring.py, matching.py) that routes call into. Keeping logic out of the
routes keeps the route handlers thin (parse request -> call service ->
return JSON) and makes the logic itself testable without spinning up Flask.
"""
