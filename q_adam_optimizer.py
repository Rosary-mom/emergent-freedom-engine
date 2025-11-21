import torch
import torch.nn as nn
import torch.optim as optim

class QAdamOptimizer(optim.Optimizer):
    def __init__(self, params, Q=1):
        defaults = dict(Q=Q)
        super().__init__(params, defaults)

    def step(self, closure=None):
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None:
                    continue
                grad = p.grad.data

                # Q-Hebel-Korrektur: Strafe für Abweichung von 1/2
                q_penalty = torch.abs(p.data - 0.5) * group['Q']
                grad = grad + q_penalty

                # Klassischer Adam-Schritt, aber mit 1/Q als Basis-Lernrate
                state = self.state[p]
                if len(state) == 0:
                    state['step'] = 0
                    state['m'] = torch.zeros_like(p.data)
                    state['v'] = torch.zeros_like(p.data)

                state['step'] += 1
                m, v = state['m'], state['v']
                beta1, beta2 = 0.9, 0.999
                m.mul_(beta1).add_(grad, alpha=1 - beta1)
                v.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)
                bias_correction1 = 1 - beta1 ** state['step']
                bias_correction2 = 1 - beta2 ** state['step']
                step_size = 1/group['Q'] * bias_correction1 / (bias_correction2.sqrt() + 1e-8)
                p.data.addcdiv_(m, v.sqrt() + 1e-8, value=-step_size)

        return loss

# Beispiel
model = nn.Linear(10, 1)
optimizer = QAdamOptimizer(model.parameters(), Q=1)  # Q ist unteilbar → 1
criterion = nn.MSELoss()

print("Q-Adam bereit – die kritische Linie wartet auf Dich.")
