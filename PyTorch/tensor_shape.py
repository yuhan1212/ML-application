import torch

shape = (2,3,)
rand_tensor = torch.rand(shape)
ones_tensor = torch.ones(shape)
zeros_tensor = torch.zeros(shape)

print(f"Random Tensor: \n {rand_tensor} \n")
print(f"Ones Tensor: \n {ones_tensor} \n")
print(f"Zeros Tensor: \n {zeros_tensor}")

"""
Output: 

  Random Tensor:
   tensor([[0.0034, 0.3447, 0.5966],
          [0.9442, 0.1058, 0.2222]])

  Ones Tensor:
   tensor([[1., 1., 1.],
          [1., 1., 1.]])

  Zeros Tensor:
   tensor([[0., 0., 0.],
          [0., 0., 0.]])
        
"""
