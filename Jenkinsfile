pipeline {
    stages {
        stage('Build') {
            steps {
                sh 'sed -i -e \'s/os.environ[\'\\\'\'BOT_USER_TOKEN\'\\\'\']/\'\\\'\'\'"$BOT_USER_TOKEN"\'\'\\\'\'/g\' main.py'
            }
        }
    }
}