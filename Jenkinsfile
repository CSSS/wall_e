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
                        withCredentials([
                                string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}")
                        ]) {
                            sh "docker rm -f ${testContainerName} ${testContainerDBName} || docker volume prune || true"                            
                            sh "docker image rm -f ${testContainerName.toLowerCase()} postgres python || true"          
                            sh "docker-compose up -d"
                        }
                        sleep 20
                        def containerFailed = sh script: "docker ps -a -f name=${testContainerName} --format \"{{.Status}}\" | grep 'Up'", returnStatus: true
                        def containerDBFailed = sh script: "docker ps -a -f name=${testContainerDBName} --format \"{{.Status}}\" | grep 'Up'", returnStatus: true
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