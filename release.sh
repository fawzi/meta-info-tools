if ![ -e "$HOME/.pypirc" ]; then
    echo "release requires a pypi account, and information on how to log in, in $HOME/.pypirc ."
    echo trying to generate it.
    if [ -z "$PYPI_USERNAME" ]; then
        echo -n "PYPI_USERNAME:"
        read PYPI_USERNAME
    fi
    if [ -z "$PYPI_PASSWORD" ]; then
        echo -n "PYPI_PASSWORD:"
        read PYPI_PASSWORD
    fi

    cat > "$HOME/.pypirc" <<EOF
[server-login]
username: $PYPI_USERNAME
password: $PYPI_PASSWORD
EOF
fi

pip install --upgrade pip setuptools wheel
pip install tqdm
pip install --upgrade twine

python setup.py sdist bdist_wheel
python -m twine upload dist/meta*
