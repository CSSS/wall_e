pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'sed -i -e \'s/os\\.environ\\[\'\\\'\'BOT_USER_TOKEN\'\\\'\'\\]/\'\\\'\'\'"$BOT_USER_TOKEN"\'\'\\\'\'/g\' main.py'
            }
        }
        stage('Deploy') {
            steps {
                sshPublisher(publishers: [sshPublisherDesc(configName: 'winfieldchen.me', transfers: [sshTransfer(excludes: '', execCommand: 'sudo apt --yes --force-yes install python3 python3-pip; pip3 install -r /home/ubuntu/test-bot/requirements.txt; screen -X -S \'test-bot\' kill; chmod +x /home/ubuntu/test-bot/main.py; screen -dmS \'test-bot\' bash -c \'python3 /home/ubuntu/test-bot/main.py; exec bash\'', execTimeout: 120000, flatten: false, makeEmptyDirs: false, noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: '/test-bot', remoteDirectorySDF: false, removePrefix: '', sourceFiles: '*.py,requirements.txt')], usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)])
            }
        }
    }
}