// Mock user data
interface User {
  id: string;
  email?: string;
  phone?: string;
  last_sign_in_at: string;
}

// Mocked stored users
const mockUsers = [
  {
    email: 'test@example.com',
    password: 'password123',
    id: 'user-1',
    last_sign_in_at: new Date().toISOString(),
  },
  {
    phone: '13800138000',
    id: 'user-2',
    last_sign_in_at: new Date().toISOString(),
  },
];

// Mock authentication service
export const mockAuth = {
  // Current user
  currentUser: null as User | null,

  // Email/password sign-in
  signInWithPassword: async ({
    email,
    password,
  }: {
    email: string;
    password: string;
  }) => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 1000));

    const user = mockUsers.find(
      u => u.email === email && u.password === password,
    );

    if (!user) {
      return { error: { message: '邮箱或密码错误' } };
    }

    const userData = {
      id: user.id,
      email: user.email,
      last_sign_in_at: new Date().toISOString(),
    };

    mockAuth.currentUser = userData;
    localStorage.setItem('mockUser', JSON.stringify(userData));

    return { data: { user: userData }, error: null };
  },

  // Phone login/registration - send OTP
  signInWithOtp: async ({}: { phone?: string; email?: string }) => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate successful code delivery
    return { error: null };
  },

  // Verify OTP (phone)
  verifyOtp: async ({
    phone,
    token,
  }: {
    phone?: string;
    email?: string;
    token: string;
    type: string;
  }) => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate successful code verification
    if (token === '123456' || token === '') {
      let userData;

      if (phone) {
        userData = {
          id: 'user-' + Math.floor(Math.random() * 1000),
          phone,
          last_sign_in_at: new Date().toISOString(),
        };
      } else {
        // For email verification we simply return success without creating a user
        return { data: { verified: true }, error: null };
      }

      mockAuth.currentUser = userData;
      localStorage.setItem('mockUser', JSON.stringify(userData));

      return { data: { user: userData }, error: null };
    }

    return { error: { message: '验证码错误' } };
  },

  // Sign up
  signUp: async ({ email }: { email: string; password: string }) => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate successful registration
    const userData = {
      id: 'user-' + Math.floor(Math.random() * 1000),
      email,
      last_sign_in_at: new Date().toISOString(),
    };

    mockAuth.currentUser = userData;
    localStorage.setItem('mockUser', JSON.stringify(userData));

    return { data: { user: userData }, error: null };
  },

  // Password reset email - simulate sending a verification code
  resetPasswordForEmail: async () => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate successful code delivery
    return { error: null };
  },

  // Update user
  updateUser: async ({}: { password: string }) => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate successful password update
    return { error: null };
  },

  // Fetch current user
  getUser: async () => {
    // Retrieve user from local storage
    const storedUser = localStorage.getItem('mockUser');
    const user = storedUser ? JSON.parse(storedUser) : null;
    mockAuth.currentUser = user;

    return { data: { user }, error: null };
  },

  // Sign out
  signOut: async () => {
    // Clear the user stored locally
    localStorage.removeItem('mockUser');
    mockAuth.currentUser = null;

    return { error: null };
  },
};
