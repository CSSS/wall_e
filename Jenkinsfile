pipeline {
    agent any
    stages {
        stage('Test Build') {
            steps {
                withCredentials([string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: 'TEST_BOT_USER_TOKEN')]) {
                    sh 'sed -i -e "s/YOUR_TOKEN_HERE/$TEST_BOT_USER_TOKEN/g" main.py'
                }
            }
        }
        stage('Test Deploy') {
            steps {
                sshPublisher(publishers: [sshPublisherDesc(configName: '159.89.134.71-test', transfers: [sshTransfer(excludes: '', execCommand: 'pip3 install -r /home/wall-e-test/requirements.txt; screen -X -S \'wall-e-test\' kill; chmod +x /home/wall-e-test/main.py; screen -dmS \'wall-e-test\' bash -c \'python3 /home/wall-e-test/main.py; exec bash\'', execTimeout: 120000, flatten: false, makeEmptyDirs: false, noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: '/', remoteDirectorySDF: false, removePrefix: '', sourceFiles: '*.py,requirements.txt')], usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)])
            }
        }
        stage('Build') {
            when {
                branch 'master'
            }
            steps {
                withCredentials([string(credentialsId: 'BOT_USER_TOKEN', variable: 'BOT_USER_TOKEN')]) {
                    sh 'sed -i -e "s/YOUR_TOKEN_HERE/$BOT_USER_TOKEN/g" main.py'
                }
            }
        }
        stage('Deploy') {
            when {
                branch 'master'
            }
            steps {
                sshPublisher(publishers: [sshPublisherDesc(configName: '159.89.134.71', transfers: [sshTransfer(excludes: '', execCommand: 'pip3 install -r /home/wall-e/requirements.txt; screen -X -S \'wall-e\' kill; chmod +x /home/wall-e/main.py; screen -dmS \'wall-e\' bash -c \'python3 /home/wall-e/main.py; exec bash\'', execTimeout: 120000, flatten: false, makeEmptyDirs: false, noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: '/', remoteDirectorySDF: false, removePrefix: '', sourceFiles: '*.py,requirements.txt')], usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)])
            }
        }
    }
}