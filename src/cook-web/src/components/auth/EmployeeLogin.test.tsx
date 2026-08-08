import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { EmployeeLogin } from './EmployeeLogin';

const mockLoginWithEmployee = jest.fn();

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    loginWithEmployee: mockLoginWithEmployee,
    sendSmsCode: jest.fn(),
  }),
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, values?: Record<string, unknown>) =>
      values?.count ? `${key}:${values.count}` : key,
  }),
}));

jest.mock('@/i18n', () => ({
  __esModule: true,
  default: {
    language: 'en-US',
  },
}));

jest.mock('@/hooks/useToast', () => ({
  useToast: () => ({ toast: jest.fn() }),
}));

describe('EmployeeLogin', () => {
  beforeEach(() => {
    mockLoginWithEmployee.mockReset();
    mockLoginWithEmployee.mockResolvedValue({ code: 0 });
  });

  it('renders employee number and password inputs', () => {
    render(<EmployeeLogin onLoginSuccess={() => {}} />);
    expect(screen.getByLabelText('module.auth.employeeNo')).toBeInTheDocument();
    expect(
      screen.getByLabelText('module.auth.password'),
    ).toBeInTheDocument();
  });

  it('submits employeeNo + password via loginWithEmployee', async () => {
    render(<EmployeeLogin onLoginSuccess={() => {}} />);
    fireEvent.change(screen.getByLabelText('module.auth.employeeNo'), {
      target: { value: 'sch00068' },
    });
    fireEvent.change(screen.getByLabelText('module.auth.password'), {
      target: { value: 'secret' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'module.auth.login' }));

    await waitFor(() => {
      expect(mockLoginWithEmployee).toHaveBeenCalledTimes(1);
      expect(mockLoginWithEmployee).toHaveBeenCalledWith(
        'sch00068',
        'secret',
        'en-US',
      );
    });
  });

  it('does not submit when employee number is empty', async () => {
    render(<EmployeeLogin onLoginSuccess={() => {}} />);
    fireEvent.change(screen.getByLabelText('module.auth.password'), {
      target: { value: 'secret' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'module.auth.login' }));

    await waitFor(() => {
      expect(mockLoginWithEmployee).not.toHaveBeenCalled();
    });
    expect(screen.getByText('module.auth.employeeNoEmpty')).toBeInTheDocument();
  });
});
