pipeline {
    agent {
        docker { image 'python:3.6.2' }
    }
    stages {
        stage('Build') {            
            steps {                
                echo 'Building'            
            }        
        }        
        stage('Test') {            
            steps {                
                sh 'python --version'   
            }        
        }
    }
 
    post {        
        always {            
            echo 'One way or another, I have finished'            
            deleteDir() /* clean up our workspace */        
        }        
        success {            
            echo 'I succeeeded!'        
        }        
        unstable {            
            echo 'I am unstable :/'        
        }        
        failure {            
            echo 'I failed :('        
        }        
        changed {            
            echo 'Things were different before...'        
        }    
    }
}
