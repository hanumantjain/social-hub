pipeline {
    agent any

    tools {
        nodejs 'node'
    }

    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        S3_BUCKET = 'social-frontend-app'
        LAMBDA_FUNCTION_NAME = 'social-fastapi-lambda'
        SAM_ARTIFACTS_BUCKET = 'social-backend-deploy'
        CLOUDFRONT_DISTRIBUTION_ID = 'E1N8C0FX33ALOR'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code'
                git branch: 'main', url: 'https://github.com/hanumantjain/social-hub.git'
            }
        }

        stage('Build and Deploy Client and Server') {
            parallel {
                stage('Frontend: Build & Deploy') {
                    stages {
                        stage('Build Client') {
                            steps {
                                dir('client') {
                                    sh '''
                                        echo "Building React frontend..."
                                        npm install
                                        npm run build
                                    '''
                                }
                            }
                        }
                        stage('Deploy Client to S3') {     
                            steps {
                                withAWS(credentials: 'aws-credentials-id', region: "${AWS_DEFAULT_REGION}") {
                                    dir('client/dist') {
                                        sh '''
                                            echo "Deploying to S3..."
                                            aws s3 sync . s3://${S3_BUCKET} --delete
                                        '''
                                    }
                                }
                            }
                        }
                        stage('Invalidate CloudFront Cache') {
                            steps {
                                withAWS(credentials: 'aws-credentials-id', region: "${AWS_DEFAULT_REGION}") {
                                    sh '''
                                        echo "Invalidating CloudFront cache..."
                                        aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} --paths "/*"
                                    '''
                                }
                            }
                        }
                    }
                }

                stage('Backend: Build & Deploy') {
                    stages {
                        stage('Build Server') {
                            steps {
                                dir('server') {
                                    sh '''
                                        echo "Building FastAPI backend..."
                                        sam build
                                    '''
                                }
                            }
                        }

                        stage('Deploy Server to Lambda') {
                            steps {
                                withAWS(credentials: 'aws-credentials-id', region: "${AWS_DEFAULT_REGION}") {
                                    dir('server') {
                                        sh '''
                                            echo "Deploying FastAPI backend to Lambda..."
                                            sam deploy \
                                                --stack-name ${LAMBDA_FUNCTION_NAME} \
                                                --s3-bucket ${SAM_ARTIFACTS_BUCKET} \
                                                --no-confirm-changeset \
                                                --capabilities CAPABILITY_IAM \
                                                --region ${AWS_DEFAULT_REGION}
                                        '''
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Frontend and backend successfully deployed!'
        }
        failure {
            echo 'Build or deployment failed.'
        }
    }
}
