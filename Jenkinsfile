pipeline {
    agent any
    stages {
        String tokenEnv = 'TOKEN'
        stage('Build') {
            steps {
                docker.build("wall-e:${env.BUILD_ID}")
            }
        }
        stage('Test') {
            steps {
                withCredentials([string(credentialsId: 'TEST_BOT_USER_TOKEN', variable: "${tokenEnv}")]) {
                    String testContainerName = 'wall-e-test'
                    sh "docker stop ${testContainerName}"
                    sh "docker rm ${testContainerName}"
                    sh "docker run -d -e ${tokenEnv} --name ${testContainerName} wall-e:${env.BUILD_ID}"
                }
            }
        }
        stage('Deploy') {
            when {
                branch 'master'
            }
            steps {
                withCredentials([string(credentialsId: 'BOT_USER_TOKEN', variable: "${tokenEnv}")]) {
                    String productionContainerName = 'wall-e'
                    sh "docker stop ${productionContainerName}"
                    sh "docker rm ${productionContainerName}"
                    sh "docker run -d -e ${tokenEnv} --name ${productionContainerName} wall-e:${env.BUILD_ID}"
                }
            }
        }
    }
}