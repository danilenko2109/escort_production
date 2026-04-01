import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Star, Shield, Heart } from 'lucide-react';
import HeroCitySearch from '../components/HeroCitySearch';
import ProfileCard from '../components/ProfileCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { profilesAPI } from '../utils/api';

const HomePage = () => {
  const navigate = useNavigate();
  const [featuredProfiles, setFeaturedProfiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeatured = async () => {
      try {
        const { data } = await profilesAPI.getAll({ featured_only: true });
        setFeaturedProfiles(data.slice(0, 6));
      } catch (error) {
        console.error('Error fetching featured profiles:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchFeatured();
  }, []);

  const handleCitySearch = (city) => {
    localStorage.setItem('searchCity', city);
    navigate(`/profiles?city=${encodeURIComponent(city)}`);
  };

  return (
    <div className="min-h-screen grain">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden" data-testid="hero-section">
        {/* Background */}
        <div className="absolute inset-0 z-0">
          <img
            src="https://static.prod-images.emergentagent.com/jobs/f41ef10d-503e-475e-a135-ee7599651f36/images/a73d048f61a4c0d4b149a030890d7006ebebd95b5ba4d312651dcf5f78e1a1d3.png"
            alt="Hero Background"
            className="w-full h-full object-cover opacity-30"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#050505]/50 via-[#050505]/70 to-[#050505]" />
        </div>

        {/* Decorative floating elements */}
        <motion.div
          animate={{ y: [0, -20, 0], opacity: [0.3, 0.6, 0.3] }}
          transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-[#D4AF37]/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ y: [0, 20, 0], opacity: [0.2, 0.5, 0.2] }}
          transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut', delay: 1 }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#D4AF37]/10 rounded-full blur-3xl"
        />

        {/* Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-6 md:px-12 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <p className="text-xs sm:text-sm uppercase tracking-[0.3em] font-medium text-[#D4AF37] mb-6">
              Эскорт агентство
            </p>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-medium tracking-tighter leading-none text-[#F8F8F8] mb-6" data-testid="hero-title">
              Откройте мир
              <br />
              <span className="text-[#D4AF37]">изысканности</span>
            </h1>
            <p className="text-base sm:text-lg text-[#A1A1AA] font-light leading-relaxed max-w-2xl mx-auto mb-12">
              Эксклюзивный каталог избранных профилей. Утонченность, элегантность и полная конфиденциальность для взыскательных клиентов.
            </p>
          </motion.div>

          <div className="max-w-2xl mx-auto">
            <HeroCitySearch onSearch={handleCitySearch} />
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 1 }}
            className="mt-12"
          >
            <p className="text-sm text-[#71717A] uppercase tracking-widest">
              Найдите профили рядом с вами
            </p>
          </motion.div>
        </div>
      </section>

      {/* Featured Profiles */}
      <section className="py-24 md:py-32 relative" data-testid="featured-section">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <p className="text-xs sm:text-sm uppercase tracking-[0.3em] font-medium text-[#D4AF37] mb-4">
              Избранные профили
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#F8F8F8]">
              VIP коллекция
            </h2>
          </motion.div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <LoadingSkeleton key={i} type="card" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {featuredProfiles.map((profile) => (
                <ProfileCard key={profile.id} profile={profile} />
              ))}
            </div>
          )}

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="text-center mt-12"
          >
            <button
              onClick={() => navigate('/profiles')}
              className="inline-flex items-center space-x-2 bg-transparent border border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#050505] transition-all duration-300 uppercase tracking-widest text-sm py-4 px-8"
              data-testid="view-all-profiles-button"
            >
              <span>Весь каталог</span>
              <ArrowRight size={18} />
            </button>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 md:py-32 bg-[#0A0A0A]/50" data-testid="features-section">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="text-center space-y-4"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border border-[#D4AF37]/20 bg-[#D4AF37]/5">
                <Star className="text-[#D4AF37]" size={28} strokeWidth={1.5} />
              </div>
              <h3 className="text-xl sm:text-2xl font-medium text-[#D4AF37]">
                Премиум качество
              </h3>
              <p className="text-base text-[#A1A1AA] font-light leading-relaxed">
                Тщательно отобранные профили с высочайшими стандартами качества и профессионализма
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-center space-y-4"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border border-[#D4AF37]/20 bg-[#D4AF37]/5">
                <Shield className="text-[#D4AF37]" size={28} strokeWidth={1.5} />
              </div>
              <h3 className="text-xl sm:text-2xl font-medium text-[#D4AF37]">
                Конфиденциальность
              </h3>
              <p className="text-base text-[#A1A1AA] font-light leading-relaxed">
                Полная гарантия конфиденциальности и защиты личных данных всех наших клиентов
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-center space-y-4"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border border-[#D4AF37]/20 bg-[#D4AF37]/5">
                <Heart className="text-[#D4AF37]" size={28} strokeWidth={1.5} />
              </div>
              <h3 className="text-xl sm:text-2xl font-medium text-[#D4AF37]">
                Индивидуальный подход
              </h3>
              <p className="text-base text-[#A1A1AA] font-light leading-relaxed">
                Персональный сервис и внимание к каждой детали для создания незабываемого опыта
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 md:py-32" data-testid="cta-section">
        <div className="max-w-4xl mx-auto px-6 md:px-12 text-center">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#F8F8F8] mb-6">
              Готовы начать?
            </h2>
            <p className="text-base sm:text-lg text-[#A1A1AA] font-light leading-relaxed mb-12">
              Откройте доступ к эксклюзивному каталогу премиум профилей
            </p>
            <button
              onClick={() => navigate('/contacts')}
              className="bg-transparent border border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#050505] transition-all duration-300 uppercase tracking-widest text-sm py-4 px-12"
              data-testid="contact-us-button"
            >
              Связаться с нами
            </button>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
