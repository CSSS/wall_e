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
                            "COMPOSE_PROJECT_NAME=TEST_${BRANCH_NAME}",
                            'POSTGRES_DB_USER=postgres',
                            'POSTGRES_DB_DBNAME=postgres',
                            'WALL_E_DB_USER=wall_e',
                            'WALL_E_DB_DBNAME=csss_discord_db'
                    ]) {
			GString pyTestContainerName = "${COMPOSE_PROJECT_NAME}_wall_e_pytest"
			sh "docker rm -f ${pyTestContainerName} || true"
			sh "docker image rm -f ${pyTestContainerName.toLowerCase()} || true"
			
			sh "docker build -t ${pyTestContainerName.toLowerCase()} -f Dockerfile.test ."
			sh "docker run -d -e --net=host --name ${pyTestContainerName} ${pyTestContainerName.toLowerCase()}"
			sh "return $(docker inspect ${pyTestContainerName}  --format='{{.State.ExitCode}}')"
                        sleep 20
			sh "docker logs ${pyTestContainerName}"
			
			String tokenEnv = 'TOKEN'
                        String wolframEnv = 'WOLFRAMAPI'

                        GString testContainerName = "${COMPOSE_PROJECT_NAME}_wall_e"
                        GString testContainerDBName = "${COMPOSE_PROJECT_NAME}_wall_e_db"

                        String postgresDbPassword='POSTGRES_PASSWORD'

                        String walleDbPassword='WALL_E_DB_PASSWORD'

                        withCredentials([
                                string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}"),
                                string(credentialsId: 'POSTGRES_PASSWORD', variable: "${postgresDbPassword}"),
                                string(credentialsId: 'WALL_E_DB_PASSWORD', variable: "${walleDbPassword}"),

                        ]) {
                            sh "docker rm -f ${testContainerName} ${testContainerDBName} || true"
                            sh "docker volume rm ${COMPOSE_PROJECT_NAME}_logs || true"
                            sh "docker network rm ${COMPOSE_PROJECT_NAME.toLowerCase()}_default || true"
                            sh "docker image rm -f ${testContainerName.toLowerCase()} || true"

                            sh "docker volume create --name=\"${COMPOSE_PROJECT_NAME}_logs\""
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
                            'POSTGRES_DB_USER=postgres',
                            'POSTGRES_DB_DBNAME=postgres',
                            'WALL_E_DB_USER=wall_e',
                            'WALL_E_DB_DBNAME=csss_discord_db',
                            'COMPOSE_PROJECT_NAME=PRODUCTION_MASTER'
                    ]) {
                        String tokenEnv = 'TOKEN'
                        String wolframEnv = 'WOLFRAMAPI'

                        GString productionContainerName = "${COMPOSE_PROJECT_NAME}_wall_e"
                        GString productionContainerDBName = "${COMPOSE_PROJECT_NAME}_wall_e_db"

                        String postgresDbPassword='POSTGRES_PASSWORD'

                        String walleDbPassword='WALL_E_DB_PASSWORD'

                        String logChannelEnv = 'BOT_LOG_CHANNEL_ID'
                        withCredentials([
                                string(credentialsId: 'BOT_USER_TOKEN', variable: "${tokenEnv}"),
                                string(credentialsId: 'WOLFRAMAPI', variable: "${wolframEnv}"),
                                string(credentialsId: 'BOT_LOG_CHANNEL_ID', variable: "${logChannelEnv}"),
                                string(credentialsId: 'POSTGRES_PASSWORD', variable: "${postgresDbPassword}"),
                                string(credentialsId: 'WALL_E_DB_PASSWORD', variable: "${walleDbPassword}"),
                        ]) {
                            sh "docker rm -f ${productionContainerName} || true"
                            sh "docker image rm -f ${productionContainerName.toLowerCase()} || true"
                            sh "docker volume create --name=\"${COMPOSE_PROJECT_NAME}_logs\""                                    
                            sh "docker-compose up -d"
                        }
                        sleep 20
                        def containerFailed = sh script: "docker ps -a -f name=${productionContainerName} --format \"{{.Status}}\" | head -1 | grep 'Up'", returnStatus: true
                        def containerDBFailed = sh script: "docker ps -a -f name=${productionContainerDBName} --format \"{{.Status}}\" | head -1 | grep 'Up'", returnStatus: true
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
