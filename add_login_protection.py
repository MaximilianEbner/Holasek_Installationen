#!/usr/bin/env python3
"""
Script to add @login_required decorator to all unprotected routes in app.py
"""

import re

def add_login_protection():
    # Read the current app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Routes that should NOT be protected (login-related routes)
    excluded_routes = [
        '/login',
        '/logout', 
        '/init-admin'
    ]
    
    # Find all @app.route definitions
    route_pattern = r'(\s*)(@app\.route\([^)]+\))\s*\n(\s*)(def\s+\w+\()'
    
    def replace_route(match):
        indent = match.group(1)
        route_decorator = match.group(2)
        func_indent = match.group(3)
        func_def = match.group(4)
        
        # Check if this route should be excluded
        for excluded in excluded_routes:
            if excluded in route_decorator:
                return match.group(0)  # Return unchanged
        
        # Check if @login_required is already present
        if '@login_required' in match.group(0):
            return match.group(0)  # Already protected
            
        # Add @login_required decorator
        return f"{indent}{route_decorator}\n{func_indent}@login_required\n{func_indent}{func_def}"
    
    # Apply the replacement
    new_content = re.sub(route_pattern, replace_route, content)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Login protection added to all routes in app.py")

if __name__ == "__main__":
    add_login_protection()
