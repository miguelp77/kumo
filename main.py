# Devokumo
# Imputation for Devoteam Cloud Services
import kumo
import config


app = kumo.create_app(config)


# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
