pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }
    stages {
        stage('Test') {
            steps {
                script {
                    withEnv([
                            'ENVIRONMENT=TEST',
                            "BRANCH=${BRANCH_NAME}",
                            "COMPOSE_PROJECT_NAME=${BRANCH_NAME}"
                    ]) {
                        String tokenEnv = 'TOKEN'
                        String wolframEnv = 'WOLFRAMAPI'
                        GString testContainerName = "${COMPOSE_PROJECT_NAME}_wall_e"
                        GString testContainerDBName = "${COMPOSE_PROJECT_NAME}_wall_e_db"
                        String postgresDbPassword='POSTGRES_DATABASE_PASSWORD'
                        String walleDbPassword='WALL_E_DATABASE_PASSWORD'
                        withCredentials([
                                string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}"),
                                string(credentialsId: 'POSTGRES_DB_PASSWORD', variable: "${postgresDbPassword}"),
                                string(credentialsId: 'WALL_E_DB_PASSWORD', variable: "${walleDbPassword}"),
                        ]) {
                            sh "echo COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT_NAME"
                            sh "docker rm -f ${testContainerName} ${testContainerDBName} || docker volume prune || true"                            
                            sh "docker image rm -f ${testContainerName.toLowerCase()} postgres python || true"       
                            sh "whoami"
                            sh "pwd"
                            sh "ls -l"                           
                            sh "ls -l database_config_file"
                            sh "head -10 database_config_file/backup.sql"
                            sh "ls -l database_config_file"
                            sh "./database_config_password_setter.sh"
                            sh "whoami"
                            sh "ls -l"                           
                            sh "ls -l database_config_file"
                            sh "head -20 database_config_file/backup.sql"
                            sh "ls -l database_config_file"
                            sh "docker-compose up -d"
                        }
                        sleep 20
                        def containerFailed = sh script: "docker ps -a -f name=${testContainerName} --format \"{{.Status}}\" | head -1 | grep 'Up'", returnStatus: true
                        def containerDBFailed = sh script: "docker ps -a -f name=${testContainerDBName} --format \"{{.Status}}\" | head -1 |  grep 'Up'", returnStatus: true
                        if (containerFailed) {
                            def output = sh (
                                    script: "docker logs ${testContainerName}",
                                    returnStdout: true
                            ).trim()
                            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                                discordSend description: BRANCH_NAME + '\n' + output, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: false, title: 'Failing build', webhookURL: "$WEBHOOKURL"
                            }
                            error output
                        }
                        if (containerDBFailed){
                            def output = sh (
                                    script: "docker logs ${testContainerDBName}",
                                    returnStdout: true
                            ).trim()
                            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                                discordSend description: BRANCH_NAME + '\n' + output, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: false, title: 'Failing build', webhookURL: "$WEBHOOKURL"
                            }
                            error output
                        }
                    }
                }
            }
        }
        stage('Deploy') {
            when {
                branch 'master'
            }
            steps {
                script {
                    withEnv([
                            'ENVIRONMENT=PRODUCTION',
                            "COMPOSE_PROJECT_NAME=PRODUCTION"
                    ]) {
                        String tokenEnv = 'TOKEN'
                        String wolframEnv = 'WOLFRAMAPI'
                        String logChannelEnv = 'BOT_LOG_CHANNEL_ID'
                        GString productionContainerName = "${COMPOSE_PROJECT_NAME}_wall_e"
                        GString productionContainerDBName = "${COMPOSE_PROJECT_NAME}_wall_e_db"
                        withCredentials([
                                string(credentialsId: 'BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}"),
                                string(credentialsId: 'BOT_LOG_CHANNEL_ID', variable: "${logChannelEnv}")
                        ]) {
                            sh "docker rm -f ${productionContainerName} || true"
                            sh "docker image rm -f ${productionContainerName.toLowerCase()} postgres python  || true"                                      
                            sh "docker-compose up -d"
                            //sh "docker run -d -e ${tokenEnv} -e ${wolframEnv} -e ${logChannelEnv} -e ENVIRONMENT --net=host --name ${productionContainerName} --mount source=logs,target=/usr/src/app/logs wall-e:${env.BUILD_ID}"
                        }
                        sleep 20
                        def containerFailed = sh script: "docker ps -a -f name=${productionContainerName} --format \"{{.Status}}\" | grep 'Up'", returnStatus: true
                        def containerDBFailed = sh script: "docker ps -a -f name=${productionContainerDBName} --format \"{{.Status}}\" | grep 'Up'", returnStatus: true
                        if (containerFailed) {
                            def output = sh (
                                    script: "docker logs ${productionContainerName}",
                                    returnStdout: true
                            ).trim()
                            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                                discordSend description: BRANCH_NAME + '\n' + output, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: false, title: 'Failing build', webhookURL: "$WEBHOOKURL"
                            }
                            error output
                        }
                        if (containerDBFailed){
                            def output = sh (
                                    script: "docker logs ${productionContainerDBName}",
                                    returnStdout: true
                            ).trim()
                            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                                discordSend description: BRANCH_NAME + '\n' + output, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: false, title: 'Failing build', webhookURL: "$WEBHOOKURL"
                            }
                            error output
                        }                                            
                    }
                }
            }
        }
    }
    post {
        success {
            withCredentials([string(credentialsId: 'DISCORD_WEBHOOK', variable: 'WEBHOOKURL')]) {
                discordSend description: BRANCH_NAME, footer: env.GIT_COMMIT, link: env.BUILD_URL, successful: true, title: 'Successful build', webhookURL: "$WEBHOOKURL"
            }
        }
    }
}