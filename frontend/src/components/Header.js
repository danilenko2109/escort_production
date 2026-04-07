import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Header = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { to: '/', label: 'Главная' },
    { to: '/profiles', label: 'Профили' },
    { to: '/about', label: 'О нас' },
    { to: '/contacts', label: 'Контакты' },
  ];

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6 }}
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        isScrolled
          ? 'backdrop-blur-2xl bg-[#050505]/80 border-b border-white/5'
          : 'bg-transparent'
      }`}
      data-testid="main-header"
    >
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group" data-testid="logo-link">
            <div className="h-10 w-10 rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 text-[#D4AF37] flex items-center justify-center text-xs font-semibold">LA</div>
            {/* <span className="text-2xl font-medium tracking-tight text-[#D4AF37]">
              
            </span> */}
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`text-sm uppercase tracking-widest transition-colors ${
                  location.pathname === link.to
                    ? 'text-[#D4AF37]'
                    : 'text-[#A1A1AA] hover:text-[#D4AF37]'
                }`}
                data-testid={`nav-link-${link.label}`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-[#D4AF37] p-2"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            data-testid="mobile-menu-button"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden backdrop-blur-2xl bg-[#050505]/95 border-t border-white/5"
            data-testid="mobile-menu"
          >
            <nav className="px-6 py-6 space-y-4">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`block text-sm uppercase tracking-widest transition-colors ${
                    location.pathname === link.to
                      ? 'text-[#D4AF37]'
                      : 'text-[#A1A1AA] hover:text-[#D4AF37]'
                  }`}
                  data-testid={`mobile-nav-link-${link.label}`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
};

export default Header;