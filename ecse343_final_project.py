# -*- coding: utf-8 -*-
"""ECSE343 Final Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pPYx3cjW11FNxfMu99870btT0CohoeDH
"""

# [TODO] Rename this file to [your student ID].py

# DO NOT EDIT THESE IMPORT STATEMENTS!
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy.stats import multivariate_normal
from time import sleep
##########

###########
# DO NOT edit this function
def EM(gmm):
    """
    Runs the expectation-maximization algorithm on a GMM
    
    Input: 
    gmm (Class GMM): our GMM instance
    
    Returns: 
    Nothing, but it should modify gmm using the previously defined functions
    """
    
    #Log likelihood computation
    if gmm.verbose:
        print('Iteration: {:4d}'.format(0), flush = True)

    # Compute mixture normalization for all the samples
    normalization(gmm)

    # Compute initial Log likelihoods
    logLikelihood(gmm)
          
    # Repeat EM iterations
    for n in range(1,gmm.max_iter):               
        # Expectation step
        expectation(gmm)

        # Maximization step
        maximization(gmm)
        
        # Update mixture normalization for all the samples
        normalization(gmm)
        
        # Update the Log likelihood estimate
        logLikelihood(gmm)

        # Logging and plotting
        if gmm.verbose:
            print('Iteration: {:4d} - log likelihood: {:1.6f}'.format(n, gmm.log_likelihoods[-1]), flush = True)
        
        if gmm.do_plot:
            #gmm.plotGMM(ellipse = True)
            #plt.pause(0.05)
            #sleep(0.15)
            if n != gmm.max_iter - 1:
                plt.close()
            
        # Compute the relative log-likelihood improvement and claim victory if a convergence tolerance is met
        relative_error = abs(gmm.log_likelihoods[-2] / gmm.log_likelihoods[-1])
        if (abs(1 - relative_error) < gmm.tol):
            expectation(gmm)
            if gmm.verbose:
                print('SUCCESS: Your EM process converged.', flush = True)
            return

    plt.show()

    if gmm.verbose:
        print('ERROR: You ran out of iterations before converging.', flush = True)
###########


###########
# DO NOT EDIT
# Class that encapsulates the Gaussian mixture model data and utility methods
class GMM:
    def __init__( self, X, n_components = 10, reg_covar = 1e-2, tol = 1e-4, 
                  max_iter = 100, verbose = True, do_plot = False, mu_init = None):
        """
        Constructor of the GMM class
            
        Inputs: 
        X (np.array((n_samples, n_dim))): array containing the n_samples n_dim-dimensional data samples
        n_components (int): number of mixture components for our GMM
        reg_covar (float): regularization value to add to the diagonal of the covariance matrices
        tol (float): relative log-likelihood tolerance, at which point we will terminate the iterative EM algorithm
        max_iter (int): maximum number of iterations, after which we terminate the iterative EM algorithm
        mu_init (np.array((n_components, n_dim))): array containing initial means for each Gaussian in the mixture; if None, we will sample them from X.
        verbose (bool): True to print verbose output
        do_plot (bool): True to plot GMM evolution after each EM iteration
        """

        self.X = X.astype(np.float32)
        self.n_samples, self.n_dim = self.X.shape
        self.n_components = n_components
        self.reg_covar = reg_covar**2
        self.tol = tol
        self.max_iter = max_iter
        self.verbose = verbose
        self.do_plot = do_plot
        self.reg_covar = reg_covar**2
        
        # regularization matrix
        self.reg_cov = self.reg_covar * np.identity(self.n_dim, dtype = np.float32)
        
        # initial (isotropic) covariance extent
        self.init_covar = 0.5 * (np.amax(X) - np.amin(X)) / self.n_components          
        
        # initial covariance matrix
        self.init_cov = self.init_covar * np.identity(self.n_dim, dtype = np.float32) 
                
        
        # Initialize the mu, covariance and pi values
        if mu_init is None:
            # Initialize mean vector as random element of X
            self.mu = self.X[np.random.choice(range(0,self.n_samples), self.n_components, replace=False),:]
        else:
            try:
                assert( mu_init.shape[0] == self.n_components and mu_init.shape[1] == self.n_dim )
            except:
                raise Exception('Can\'t plot if not 2D')
            
            # Initialize mean vector from the provided means mu_init
            self.mu = mu_init 
        
        # Initialize covariances as diagonal matrices (isotropic Gaussians)
        self.cov = np.zeros((self.n_components, self.n_dim, self.n_dim), dtype=np.float32)
        for c in range(self.n_components):
            self.cov[c,:,:] = self.init_cov

        # Python list of the n_components multivariate Gaussian distributions
        # The .pdf method of the Gaussian's allows you to evaluate them at a vector of input locations
        self.gauss = []
        for c in range(self.n_components):
            self.gauss.append( multivariate_normal( mean = self.mu[c,:], 
                                                    cov = self.cov[c,:,:]) )
        
        # Probabilities of selecting a specific Gaussian from the mixture
        # Initialized to uniform probability for selecting each Gaussian, i.e., 1/K
        self.pi = np.full(self.n_components, 1./self.n_components, dtype = np.float32)
        
        # The weight of each Gaussian in the mixture
        # Initialized to 0
        self.weight = np.zeros(self.n_components, dtype = np.float32)
        
        # The probabilities of sample X_i belonging to Gaussian N_c
        # Initialized to 0
        self.alpha = np.zeros((self.n_samples, self.n_components), dtype = np.float32)
        
        # Normalization for alpha
        # Initialized to 0
        self.beta = np.zeros(self.n_samples)
        
        # Latent labels (indices) of the Gaussian with maximum probability of having generated sample X_i
        # Initialized to 0
        self.Z = np.zeros(self.n_samples, dtype = np.int32)
        
        # Python list for logging the log-likelihood after each iteration of the EM algorithm
        self.log_likelihoods = [] 

#############



# [TODO] Deliverable 4: Computing the mixture normalization
def normalization(gmm):     
    """
    Compute the mixture normalization factor for all the data samples

    Input: 
    gmm (Class GMM): our GMM instance

    Returns: 
    Nothing, but you should modify gmm.beta
    """

    ### BEGIN SOLUTION
    n=gmm.n_samples
    K=gmm.n_components
    for i in range(n):
      gmm.beta[i]=0
      for c in range(K):
        gmm.beta[i]=gmm.beta[i]+gmm.pi[c]*multivariate_normal.pdf(gmm.X[i],gmm.mu[c],gmm.cov[c])


    ### END SOLUTION



# [TODO] Deliverable 5: E-Step
def expectation(gmm):           
    """
    The expectation step

    Input:
    gmm (Class GMM): our GMM instance

    Returns: 
    Nothing, but you should modify gmm.alpha
    """

    m=gmm.n_samples
    n=gmm.n_components
    ### BEGIN SOLUTION
    for i in range(m):
      for j in range(n):
        gmm.alpha[i,j]=gmm.pi[j]*multivariate_normal.pdf(gmm.X[i],gmm.mu[j],gmm.cov[j])/gmm.beta[i]
    ### END SOLUTION



# [TODO] Deliverable 6: M-Step
def maximization(gmm):                   
    """
    The maximization step
    
    Input: 
    gmm (Class GMM): our GMM instance
    
    Returns: 
    Nothing, but you should modify gmm.Z, gmm.weight, gmm.pi, gmm.mu, gmm.cov, and gmm.gauss    
    """
    
    # You can loop over the mixture components ONLY
    # and assume that you already know alpha
    # Hint 1: np.argmax is useful, here
    # Hint 2: don't forgot to regularize your covariance matrices with gmm.reg_cov
    
    ### BEGIN SOLUTION

    gmm.Z=np.argmax(gmm.alpha,1)
    gmm.gauss=[]
    for j in range(gmm.n_components):
      gmm.weight[j]=np.sum(gmm.alpha[:,j])
      gmm.pi[j]=gmm.weight[j]/gmm.n_samples

    for j in range (gmm.n_components):
      tmp=np.zeros(3)
      for i in range(gmm.n_samples):
        tmp=tmp+gmm.alpha[i,j]*gmm.X[i]
      gmm.mu[j]=1/gmm.weight[j]*tmp
      
    for j in range(gmm.n_components):
      sum=np.zeros((3,3))
      for i in range(gmm.n_samples):
        sum=sum+gmm.alpha[i,j]*np.dot(np.reshape((gmm.X[i]-gmm.mu[j]),(gmm.X[i].shape[0],1)),np.reshape((gmm.X[i]-gmm.mu[j]),(1,gmm.X[i].shape[0])))
      gmm.cov[j]=1/gmm.weight[j]*sum+gmm.reg_cov
      gmm.gauss.append(multivariate_normal(gmm.mu[j,:],gmm.cov[j,:,:]))
    
    

    ### END SOLUTION


# [TODO] Deliverable 7: Compute the log-likelihood
def logLikelihood(gmm):                        
    """
    Log-likelihood computation

    Input: 
    gmm (Class GMM): our GMM instance

    Returns: 
    Nothing, but you should modify gmm.log_likelihoods
    """

    # Note: you need to append to gmm.log_likelihoods
    
    ### BEGIN SOLUTION
    log_llh=0
    for i in range(gmm.n_samples):
      log_llh=log_llh+np.log(gmm.beta[i])
    gmm.log_likelihoods.append(log_llh)
    ### END SOLUTION



# Some example test routines for the deliverables. 
# Feel free to write and include your own tests here.
# Code in this main block will not count for credit, 
# but the collaboration and plagiarism policies still hold.

import cv2
######################
#Read the Image in
home=cv2.imread('home.jpg')
#Adjust the RGB value for the display
home=cv2.cvtColor(home, cv2.COLOR_BGR2RGB)
#Adjust the size of the input image 
#home=cv2.resize(home,(128,96),interpolation = cv2.INTER_AREA)
height, width, channel=home.shape

#Set the number of segment color 
n_components=5
#Set the numbers of iterations from downscale/upscale for speed up
iterations=5

#Initialize the temporary variables for the iteration
tmpZ=np.zeros((int (width/(2**6)),int (height/(2**6))))
tmpmu=np.zeros((n_components,channel))
tmpcov=np.zeros((n_components, channel, channel), dtype=np.float32)
tmppi=np.full(n_components, 1./n_components, dtype = np.float32)

#Downscale the resolution of the image and process to obtain the approximate GMM model within 
#short period of time, use the obtained GMM model and  upscale the image so that the model processing
#doesn't start from the pure beginning. Iterate the same until the image resolution is back to the original resolution

for numiter in range(iterations):
  #Set tmphome as the resized version of home corresponding to which iteration the loop gets to
  tmphome=cv2.resize(home,(int(width/(2**(iterations-numiter-1))),int(height/(2**(iterations-numiter-1)))),interpolation = cv2.INTER_AREA)
  tmph, tmpw, tmpc= tmphome.shape
  tmphome=tmphome.reshape(tmph*tmpw,tmpc)
  maxiter=100
  if numiter>(iterations-3) and numiter<(iterations-2):
    maxiter=70
  elif numiter==(iterations-2):
    maxiter=20
  elif numiter==(iterations-1):
    maxiter=10
  #Initialize the GMM model
  gmm_test=GMM( tmphome, n_components, reg_covar = 1e-3, 
                    tol = 1e-6, max_iter = maxiter, 
                    verbose = True, do_plot = True) 
  #Replace the initial value of Z, mu, cov and pi with the values obtained from the last iteration
  if(numiter!=0):
    newZ=np.zeros((tmpw,tmph), dtype = np.int32)
    for i in range(tmpw):
      for j in range(tmph):
        newZ[i,j]= tmpZ[int (i/2),int (j/2)]
    newZ=newZ.reshape(tmpw*tmph)
    gmm_test.Z=newZ
    gmm_test.mu=tmpmu
    gmm_test.cov=tmpcov
    gmm_test.pi=tmppi

  EM(gmm_test)  
  # Record the Z, mu, cov, pi values for the next iteration
  tmpZ=gmm_test.Z.reshape(tmpw,tmph)
  tmpmu=gmm_test.mu
  tmpcov=gmm_test.cov
  tmppi=gmm_test.pi
  
home = home.reshape(height*width,channel)
#Replace the pixel values of the original image with the mean values
for i in range(height*width):
  home[i,:]=gmm_test.mu[gmm_test.Z[i]]

home=home.reshape(height,width,channel)
plt.imshow(home)

cv2.imwrite('resultimg.jpg',cv2.cvtColor(home, cv2.COLOR_RGB2BGR))